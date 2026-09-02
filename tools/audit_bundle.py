#!/usr/bin/env python3
"""Static privacy audit for Android .aspk/.apks-style bundles.

No third-party Python modules are required. The script extracts nested APKs,
examines DEX/native-library printable strings, and reports privacy/network
indicators. It does not claim that a string hit proves an active call path;
results are triage input for decompilation and runtime verification.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

PATTERNS = {
    "clearcut": re.compile(r"clearcut", re.I),
    "primes": re.compile(r"\bprimes\b|recordNetworkMetricsToPrimes", re.I),
    "phenotype": re.compile(r"phenotype", re.I),
    "federated_learning": re.compile(r"federat|brella|training_cache", re.I),
    "telemetry": re.compile(r"telemetry", re.I),
    "analytics_metrics": re.compile(r"analytics|metric|logging|logevent", re.I),
    "crash_diagnostics": re.compile(r"crash|diagnostic|feedback|perfetto", re.I),
    "network": re.compile(r"https?://|server_url|baseUrl|urlToDownload|URLConnection", re.I),
}

PRINTABLE = re.compile(rb"[\x20-\x7e]{5,}")


def extract_strings(path: Path):
    data = path.read_bytes()
    for m in PRINTABLE.finditer(data):
        yield m.group().decode("utf-8", "replace")


def audit_apk(apk: Path, out):
    with zipfile.ZipFile(apk) as zf:
        interesting = [
            n for n in zf.namelist()
            if re.fullmatch(r"classes\d*\.dex", Path(n).name)
            or n.endswith(".so")
        ]
        for member in interesting:
            with zf.open(member) as src:
                data = src.read()
            for m in PRINTABLE.finditer(data):
                s = m.group().decode("utf-8", "replace")
                for category, rx in PATTERNS.items():
                    if rx.search(s):
                        out[apk.name][category].add(s[:500])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bundle", type=Path)
    p.add_argument("--max-per-category", type=int, default=80)
    args = p.parse_args()

    report = defaultdict(lambda: defaultdict(set))
    with tempfile.TemporaryDirectory(prefix="keyboard-audit-") as td:
        root = Path(td)
        with zipfile.ZipFile(args.bundle) as zf:
            zf.extractall(root)
        apks = sorted(root.rglob("*.apk"))
        if not apks:
            raise SystemExit("No nested APKs found")
        for apk in apks:
            audit_apk(apk, report)

    for apk in sorted(report):
        print(f"\n===== {apk} =====")
        for category in PATTERNS:
            hits = sorted(report[apk].get(category, ()))
            if not hits:
                continue
            print(f"\n[{category}] {len(hits)} unique hits")
            for hit in hits[: args.max_per_category]:
                print("  " + hit.replace("\n", "\\n"))
            if len(hits) > args.max_per_category:
                print(f"  ... {len(hits) - args.max_per_category} more")


if __name__ == "__main__":
    main()
