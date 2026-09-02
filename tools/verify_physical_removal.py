#!/usr/bin/env python3
"""Fail a privacy build when known telemetry implementation residue remains.

This is intentionally stricter than a network blocklist check.  It scans decoded
Android trees, APKs, and ASPK/APKS-style bundles for implementation markers that
should be physically absent after the removal pass.

A passing result is a necessary gate, not proof by itself: manual call-graph and
runtime network verification are still required by PHYSICAL_REMOVAL_POLICY.md.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[bytes]
    why: str


# These are deliberately specific enough to indicate the telemetry systems
# targeted by this project. Generic words such as "log" or "metric" are not
# blanket-banned because they can describe purely local/non-telemetry behavior.
RULES = (
    Rule("clearcut", re.compile(rb"clearcut", re.I), "Google Clearcut logging/transport residue"),
    Rule("primes", re.compile(rb"(?:\bprimes\b|recordNetworkMetricsToPrimes)", re.I), "Primes telemetry residue"),
    Rule("phenotype", re.compile(rb"(?:com[./]google[./]android[./]gms[./]phenotype|\bPHENOTYPE\b|phenotype flags)", re.I), "remote Phenotype/experiment machinery residue"),
    Rule("brella", re.compile(rb"brella", re.I), "Brella/federated-learning integration residue"),
    Rule("federated_learning", re.compile(rb"(?:FederatedLearning|FederatedResult|federated[_ -]?learning)", re.I), "federated learning/training residue"),
    Rule("training_cache", re.compile(rb"training_cache", re.I), "background training cache residue"),
    Rule("enable_telemetry", re.compile(rb"android[./]net[./]http[./]EnableTelemetry", re.I), "Android HTTP telemetry registration residue"),
    Rule("telemetry_symbol", re.compile(rb"(?:^|[^A-Za-z])telemetry(?:[^A-Za-z]|$)", re.I), "explicit telemetry implementation/configuration residue"),
    Rule("network_primes", re.compile(rb"networkMetricsToPrimes", re.I), "Primes network reporting residue"),
    Rule("perfetto_trigger", re.compile(rb"Triggering Perfetto trace", re.I), "telemetry-specific trace trigger residue"),
    Rule("metrics_processor", re.compile(rb"MetricsProcessor", re.I), "keyboard metrics processor implementation requires removal/review"),
    Rule("experiment_training_id", re.compile(rb"training_cache_experiment_id", re.I), "training experiment machinery residue"),
)

SCANNABLE_SUFFIXES = {
    ".smali", ".xml", ".json", ".txt", ".properties", ".cfg", ".conf",
    ".proto", ".java", ".kt", ".dex", ".so",
}

MAX_FILE_BYTES = 256 * 1024 * 1024


@dataclass
class Hit:
    rule: Rule
    location: str
    sample: bytes


def sample_around(data: bytes, match: re.Match[bytes], radius: int = 90) -> bytes:
    start = max(0, match.start() - radius)
    end = min(len(data), match.end() + radius)
    return data[start:end].replace(b"\n", b" ").replace(b"\r", b" ")


def scan_bytes(data: bytes, location: str) -> list[Hit]:
    hits: list[Hit] = []
    for rule in RULES:
        m = rule.pattern.search(data)
        if m:
            hits.append(Hit(rule, location, sample_around(data, m)))
    return hits


def should_scan_path(path: Path) -> bool:
    if path.name == "AndroidManifest.xml":
        return True
    return path.suffix.lower() in SCANNABLE_SUFFIXES


def scan_directory(root: Path) -> list[Hit]:
    hits: list[Hit] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()

        # A telemetry-named implementation path is itself evidence even if its
        # contents are optimized/obfuscated.
        path_bytes = rel.encode("utf-8", "replace")
        hits.extend(scan_bytes(path_bytes, f"path:{rel}"))

        if not should_scan_path(path):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            print(f"warning: skipping oversized file {rel}", file=sys.stderr)
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            print(f"warning: cannot read {rel}: {exc}", file=sys.stderr)
            continue
        hits.extend(scan_bytes(data, rel))
    return hits


def scan_apk_bytes(data: bytes, label: str) -> list[Hit]:
    hits: list[Hit] = []
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return scan_bytes(data, label)

    with zf:
        for name in zf.namelist():
            name_bytes = name.encode("utf-8", "replace")
            hits.extend(scan_bytes(name_bytes, f"{label}!path:{name}"))

            leaf = Path(name).name
            suffix = Path(name).suffix.lower()
            if not (
                re.fullmatch(r"classes\d*\.dex", leaf)
                or suffix == ".so"
                or leaf == "AndroidManifest.xml"
                or suffix in {".xml", ".json", ".properties", ".proto"}
            ):
                continue
            info = zf.getinfo(name)
            if info.file_size > MAX_FILE_BYTES:
                print(f"warning: skipping oversized archive member {label}!{name}", file=sys.stderr)
                continue
            try:
                member = zf.read(name)
            except Exception as exc:  # corrupted member should be visible but not crash triage
                print(f"warning: cannot read {label}!{name}: {exc}", file=sys.stderr)
                continue
            hits.extend(scan_bytes(member, f"{label}!{name}"))
    return hits


def scan_archive(path: Path) -> list[Hit]:
    data = path.read_bytes()
    # APK itself.
    if path.suffix.lower() == ".apk":
        return scan_apk_bytes(data, path.name)

    # ASPK/APKS/ZIP bundle: recursively inspect nested APK members plus bundle
    # metadata.  Nested APKs are common for split delivery.
    hits: list[Hit] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                name_bytes = name.encode("utf-8", "replace")
                hits.extend(scan_bytes(name_bytes, f"{path.name}!path:{name}"))
                if name.lower().endswith(".apk"):
                    member = zf.read(name)
                    hits.extend(scan_apk_bytes(member, f"{path.name}!{name}"))
                elif Path(name).suffix.lower() in {".json", ".xml", ".properties", ".txt"}:
                    hits.extend(scan_bytes(zf.read(name), f"{path.name}!{name}"))
        return hits
    except zipfile.BadZipFile:
        return scan_bytes(data, path.name)


def dedupe_hits(hits: Iterable[Hit]) -> list[Hit]:
    seen: set[tuple[str, str]] = set()
    out: list[Hit] = []
    for hit in hits:
        key = (hit.rule.name, hit.location)
        if key in seen:
            continue
        seen.add(key)
        out.append(hit)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target", type=Path, help="decoded directory, APK, or ASPK/APKS bundle")
    p.add_argument("--max-hits", type=int, default=200)
    args = p.parse_args()

    target = args.target
    if not target.exists():
        print(f"error: target does not exist: {target}", file=sys.stderr)
        return 2

    if target.is_dir():
        hits = scan_directory(target)
    else:
        hits = scan_archive(target)

    hits = dedupe_hits(hits)
    if not hits:
        print("PASS: no known targeted telemetry implementation markers found.")
        print("Manual call-graph/native review and runtime network verification are still required.")
        return 0

    print(f"FAIL: found {len(hits)} telemetry-removal gate hit(s).")
    for hit in hits[: args.max_hits]:
        sample = hit.sample.decode("utf-8", "replace")
        print(f"\n[{hit.rule.name}] {hit.location}")
        print(f"  reason: {hit.rule.why}")
        print(f"  sample: {sample[:300]}")
    if len(hits) > args.max_hits:
        print(f"\n... {len(hits) - args.max_hits} additional hit(s) omitted")

    print("\nPhysical removal is incomplete. Do not ship or label this build telemetry-free.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
