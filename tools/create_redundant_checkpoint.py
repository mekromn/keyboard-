#!/usr/bin/env python3
"""Create a verified, redundant Meboard recovery checkpoint.

The checkpoint is split deliberately:

* PUBLIC: replay scripts, reports, hashes, and non-secret tooling.
* PRIVATE: original/rebuilt application binaries and signing material.

The script never uploads anything and never writes into GitHub. It creates
independent byte-for-byte copies, verifies every copy by SHA-256, emits
machine-readable state, creates ZIP recovery archives, and mirrors those ZIPs
as separate files so a later step can export them to another storage surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

CHUNK = 8 * 1024 * 1024


@dataclass(frozen=True)
class Entry:
    category: str
    source: str
    stored_as: str
    size: int
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(path: Path) -> str:
    return path.name.replace(os.sep, "_")


def copy_verified(source: Path, destination: Path) -> Entry:
    if not source.is_file():
        raise FileNotFoundError(f"required checkpoint input is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = sha256_file(source)
    shutil.copy2(source, destination)
    copied_hash = sha256_file(destination)
    if source_hash != copied_hash:
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            f"copy verification failed for {source}: {source_hash} != {copied_hash}"
        )
    return Entry(
        category="",
        source=str(source.resolve()),
        stored_as=str(destination),
        size=destination.stat().st_size,
        sha256=copied_hash,
    )


def zip_tree(source_root: Path, output: Path, include_private: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        for path in sorted(source_root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source_root)
            if not include_private and rel.parts and rel.parts[0] == "private":
                continue
            zf.write(path, rel.as_posix())
    with zipfile.ZipFile(output, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity verification failed at member: {bad}")


def write_sha256s(root: Path, entries: Iterable[Entry]) -> None:
    lines = [
        f"{entry.sha256}  {entry.stored_as}"
        for entry in sorted(entries, key=lambda e: e.stored_as)
    ]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("/mnt/data/meboard-redundant-checkpoints"),
    )
    parser.add_argument("--timestamp", help="UTC compact timestamp, e.g. 20260904T231709Z")
    parser.add_argument("--github-repository", default="mekromn/keyboard-")
    parser.add_argument("--github-ref", default="meboard/offline-continuation-20260904")
    parser.add_argument("--github-commit", required=True)
    parser.add_argument("--public", action="append", default=[], type=Path)
    parser.add_argument("--private", action="append", default=[], type=Path)
    parser.add_argument("--historical-stage18b-sha256")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final_root = args.checkpoint_root / timestamp
    if final_root.exists():
        raise SystemExit(f"refusing to overwrite existing immutable checkpoint: {final_root}")

    args.checkpoint_root.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=f".{timestamp}.", dir=args.checkpoint_root))
    entries: list[Entry] = []
    try:
        for category, paths in (("public", args.public), ("private", args.private)):
            seen: dict[str, int] = {}
            for source in paths:
                name = safe_name(source)
                count = seen.get(name, 0)
                seen[name] = count + 1
                if count:
                    stem, suffix = Path(name).stem, Path(name).suffix
                    name = f"{stem}.{count + 1}{suffix}"
                destination = temp_root / category / name
                entry = copy_verified(source, destination)
                entries.append(
                    Entry(
                        category=category,
                        source=entry.source,
                        stored_as=str(destination.relative_to(temp_root)),
                        size=entry.size,
                        sha256=entry.sha256,
                    )
                )

        state = {
            "schema": 1,
            "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checkpoint_id": timestamp,
            "project": "Meboard",
            "stage_label": args.stage,
            "github": {
                "repository": args.github_repository,
                "ref": args.github_ref,
                "commit": args.github_commit,
            },
            "highest_apk_physically_present_at_capture": "stage16-signature-guard-fix",
            "stage18b": {
                "historical_reported_sha256": args.historical_stage18b_sha256,
                "artifact_present_at_capture": False,
                "status": (
                    "must be reconstructed and reverified; "
                    "do not relabel Stage 16 as Stage 18B"
                ),
            },
            "privacy_contract": {
                "preserve": [
                    "all user-facing keyboard features",
                    "local and on-device AI/model behavior",
                    "Japanese/Mozc input, dictionaries, candidates, and local learning",
                    "user-triggered networking required by retained features",
                ],
                "remove_physically": [
                    "Google-account association and AccountManager discovery",
                    "background telemetry, analytics, diagnostics, and reporting transports",
                    "federated training/result upload and local-model data sharing",
                    "unnecessary background network connections",
                ],
            },
            "private_material_policy": {
                "github_public_upload": False,
                "signing_key_in_public_archive": False,
                "original_or_rebuilt_apk_in_public_archive": False,
            },
            "files": [asdict(entry) for entry in entries],
        }
        (temp_root / "CURRENT_STATE.json").write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        state_md = f"""# Meboard recovery checkpoint {timestamp}

- Stage label: **{args.stage}**
- GitHub source: `{args.github_repository}` ref `{args.github_ref}` at `{args.github_commit}`
- Highest APK physically present when captured: **Stage 16 signature-guard fix**
- Stage 18B APK: **not present in this runtime**; any historical hash is recorded only as a reconstruction target, never as proof that the artifact survived.
- Public and private materials are separated. The public set contains no source APK/ASPK, rebuilt APK, or signing key.
- Every copied file and every archive is SHA-256 verified.

The checkpoint is complete only when the raw checkpoint directory, both exported ZIPs, and at least one external persistent copy exist.
"""
        (temp_root / "CURRENT_STATE.md").write_text(state_md, encoding="utf-8")

        for meta_name in ("CURRENT_STATE.json", "CURRENT_STATE.md"):
            path = temp_root / meta_name
            entries.append(
                Entry(
                    category="metadata",
                    source="generated",
                    stored_as=meta_name,
                    size=path.stat().st_size,
                    sha256=sha256_file(path),
                )
            )
        write_sha256s(temp_root, entries)

        temp_root.rename(final_root)

        public_zip = Path("/mnt/data") / f"Meboard-Checkpoint-{timestamp}-PUBLIC.zip"
        private_zip = Path("/mnt/data") / f"Meboard-Checkpoint-{timestamp}-PRIVATE.zip"
        zip_tree(final_root, public_zip, include_private=False)
        zip_tree(final_root, private_zip, include_private=True)

        mirror_root = args.checkpoint_root / "archive-mirror"
        mirror_root.mkdir(parents=True, exist_ok=True)
        public_mirror = mirror_root / public_zip.name
        private_mirror = mirror_root / private_zip.name
        shutil.copy2(public_zip, public_mirror)
        shutil.copy2(private_zip, private_mirror)

        archive_records = []
        for original, mirror in ((public_zip, public_mirror), (private_zip, private_mirror)):
            original_hash = sha256_file(original)
            mirror_hash = sha256_file(mirror)
            if original_hash != mirror_hash:
                raise RuntimeError(f"archive mirror verification failed: {original} -> {mirror}")
            archive_records.append(
                {
                    "path": str(original),
                    "mirror": str(mirror),
                    "size": original.stat().st_size,
                    "sha256": original_hash,
                    "zip_integrity": "passed",
                }
            )

        completion = {
            "status": "complete",
            "checkpoint_directory": str(final_root),
            "archives": archive_records,
        }
        completion_path = Path("/mnt/data") / f"Meboard-Checkpoint-{timestamp}-RESULT.json"
        completion_path.write_text(
            json.dumps(completion, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(completion, indent=2, sort_keys=True))
        return 0
    except Exception:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
        raise


if __name__ == "__main__":
    sys.exit(main())
