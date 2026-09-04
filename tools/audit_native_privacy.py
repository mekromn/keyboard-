#!/usr/bin/env python3
"""Inventory native privacy-sensitive symbols, strings, sections, and ranges.

This tool does not patch an ELF file. It produces the evidence needed for a
surgical native excision: symbol address/size, section mapping, file offsets,
nearby JNI-registration strings, and relocation references. Matching a word is
not by itself proof that a path is executable, so findings remain categorized
until their reachability and retained-feature dependencies are established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

PATTERN = re.compile(
    r"(?i)(federat|flrunner|training.?cache|clearcut|primes|telemetry|analytics|"
    r"perfetto|native.?crash|metric|brella|example.?store|local.?computation.?result)"
)
PRINTABLE = re.compile(rb"[\x20-\x7e]{5,}")


def command(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def printable_matches(data: bytes) -> list[dict]:
    out = []
    for match in PRINTABLE.finditer(data):
        text = match.group().decode("utf-8", "replace")
        if PATTERN.search(text):
            out.append({"offset": match.start(), "offset_hex": hex(match.start()), "text": text[:2000]})
    return out


def parse_symbols(readelf: str) -> list[dict]:
    entries = []
    rx = re.compile(
        r"^\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)$"
    )
    for line in readelf.splitlines():
        match = rx.match(line)
        if not match:
            continue
        value, size, kind, bind, visibility, index, name = match.groups()
        if PATTERN.search(name):
            entries.append(
                {
                    "value": int(value, 16),
                    "value_hex": "0x" + value,
                    "size": int(size),
                    "type": kind,
                    "bind": bind,
                    "visibility": visibility,
                    "section_index": index,
                    "name": name.strip(),
                    "raw": line.strip(),
                }
            )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = {"libraries": []}
    for path in args.paths:
        if not path.is_file():
            raise SystemExit(f"missing ELF: {path}")
        data = path.read_bytes()
        item = {
            "path": str(path),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "matching_strings": printable_matches(data),
        }
        try:
            item["matching_symbols"] = parse_symbols(command("readelf", "-Ws", str(path)))
            item["sections"] = [line.strip() for line in command("readelf", "-WS", str(path)).splitlines()]
            item["matching_relocations"] = [
                line.strip() for line in command("readelf", "-Wr", str(path)).splitlines() if PATTERN.search(line)
            ]
            item["dynamic_entries"] = [
                line.strip() for line in command("readelf", "-Wd", str(path)).splitlines()
            ]
        except (OSError, subprocess.CalledProcessError) as exc:
            item["tool_error"] = repr(exc)
        report["libraries"].append(item)
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if args.json:
        args.json.write_text(encoded + "\n")
    print(encoded)


if __name__ == "__main__":
    main()
