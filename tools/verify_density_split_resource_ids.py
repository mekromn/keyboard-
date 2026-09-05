#!/usr/bin/env python3
"""Verify exact xxhdpi split ID preservation and restored binary XML references."""
from __future__ import annotations

import importlib.util
import re
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work')
TOOLS = Path(__file__).resolve().parent
AAPT2 = Path('/mnt/data/meboard_tools/android/build-tools/aapt2')
APK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'checkpoints/Meboard-launchfix-unsigned.apk'
RESTORE = TOOLS / 'restore_density_split_resource_ids.py'
DENSITY_PUBLIC = ROOT / 'decoded/density/res/values/public.xml'


def load_repairs():
    spec = importlib.util.spec_from_file_location('density_restore', RESTORE)
    if spec is None or spec.loader is None:
        raise SystemExit(f'cannot import {RESTORE}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.REPAIRS


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from('<H', data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]


def len8(data: bytes, offset: int) -> tuple[int, int]:
    value = data[offset]
    offset += 1
    if value & 0x80:
        return ((value & 0x7f) << 8) | data[offset], offset + 1
    return value, offset


def len16(data: bytes, offset: int) -> tuple[int, int]:
    value = u16(data, offset)
    offset += 2
    if value & 0x8000:
        return ((value & 0x7fff) << 16) | u16(data, offset), offset + 2
    return value, offset


def strings(data: bytes, offset: int) -> tuple[list[str], int]:
    if u16(data, offset) != 0x0001:
        raise SystemExit('binary XML string pool missing')
    header = u16(data, offset + 2)
    size = u32(data, offset + 4)
    count = u32(data, offset + 8)
    flags = u32(data, offset + 16)
    start = u32(data, offset + 20)
    offsets = [u32(data, offset + header + 4 * i) for i in range(count)]
    base = offset + start
    result: list[str] = []
    utf8 = bool(flags & 0x100)
    for relative in offsets:
        pos = base + relative
        if utf8:
            _, pos = len8(data, pos)
            byte_count, pos = len8(data, pos)
            result.append(data[pos : pos + byte_count].decode('utf-8', 'replace'))
        else:
            char_count, pos = len16(data, pos)
            result.append(data[pos : pos + char_count * 2].decode('utf-16le', 'replace'))
    return result, size


def xml_attributes(data: bytes) -> list[dict[str, object]]:
    if u16(data, 0) != 0x0003:
        raise SystemExit('not Android binary XML')
    total = u32(data, 4)
    offset = u16(data, 2)
    pool: list[str] | None = None
    result: list[dict[str, object]] = []
    while offset < total:
        chunk_type = u16(data, offset)
        header = u16(data, offset + 2)
        size = u32(data, offset + 4)
        if chunk_type == 0x0001:
            pool, _ = strings(data, offset)
        elif chunk_type == 0x0102:
            if pool is None:
                raise SystemExit('start element before string pool')
            line = u32(data, offset + 8)
            ext = offset + header
            element = pool[u32(data, ext + 4)]
            attr_start = u16(data, ext + 8)
            attr_size = u16(data, ext + 10)
            attr_count = u16(data, ext + 12)
            first = ext + attr_start
            for index in range(attr_count):
                pos = first + index * attr_size
                name_index = u32(data, pos + 4)
                result.append(
                    {
                        'line': line,
                        'element': element,
                        'attr': pool[name_index],
                        'type': data[pos + 15],
                        'data': u32(data, pos + 16),
                    }
                )
        if size <= 0:
            raise SystemExit(f'invalid binary XML chunk at {offset}')
        offset += size
    return result


def density_public_entries() -> dict[int, tuple[str, str]]:
    entries: dict[int, tuple[str, str]] = {}
    for line in DENSITY_PUBLIC.read_text().splitlines():
        match = re.search(
            r'<public type="([^"]+)" name="([^"]+)" id="0x([0-9a-f]+)"',
            line,
        )
        if not match:
            continue
        rid = int(match.group(3), 16)
        name = match.group(2).replace('APKTOOL_DUMMY_0x', 'APKTOOL_RENAMED_0x')
        entries[rid] = (match.group(1), name)
    return entries


def compiled_resources() -> tuple[dict[int, tuple[str, str]], dict[int, str], dict[str, list[int]]]:
    proc = subprocess.run(
        [str(AAPT2), 'dump', 'resources', str(APK)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    resources: dict[int, tuple[str, str]] = {}
    files: dict[int, str] = {}
    names: dict[str, list[int]] = {}
    current: int | None = None
    for line in proc.stdout.splitlines():
        match = re.match(r'^\s*resource (0x[0-9a-f]+) ([^/\s]+)/([^\s]+)', line)
        if match:
            current = int(match.group(1), 16)
            rtype, name = match.group(2), match.group(3)
            resources[current] = (rtype, name)
            names.setdefault(f'{rtype}/{name}', []).append(current)
            continue
        match = re.match(r'^\s*\(.*?\) \(file\) (\S+) type=XML', line)
        if match and current is not None:
            files[current] = match.group(1)
            current = None
    return resources, files, names


def main() -> None:
    for path in (APK, AAPT2, RESTORE, DENSITY_PUBLIC):
        if not path.is_file():
            raise SystemExit(f'missing verifier input: {path}')
    repairs = load_repairs()
    compiled, xml_files, by_name = compiled_resources()
    density = density_public_entries()

    expected_missing = {
        rid: value
        for rid, value in density.items()
        if value[0] != 'attr' and not (value[0] == 'style' and rid == 0x7f15017a)
    }
    if len(expected_missing) != 114:
        raise SystemExit(f'expected 114 density-only resource IDs, found {len(expected_missing)}')
    for rid, expected in sorted(expected_missing.items()):
        actual = compiled.get(rid)
        if actual != expected:
            raise SystemExit(f'compiled density ID mismatch 0x{rid:08x}: {actual} != {expected}')
        ids = by_name.get(f'{expected[0]}/{expected[1]}', [])
        if ids != [rid]:
            raise SystemExit(f'density resource name is not unique at original ID: {expected} -> {ids}')

    by_xml: dict[int, list[tuple[int, str, int]]] = {}
    for rel, line, attr, _replacement, target in repairs:
        match = re.search(r'APKTOOL_RENAMED_0x([0-9a-f]{8})\.xml$', rel)
        if match:
            xml_id = int(match.group(1), 16)
        else:
            path = Path(rel)
            if len(path.parts) < 3 or path.parts[0] != 'res' or path.suffix != '.xml':
                raise SystemExit(f'cannot derive XML resource identity from {rel}')
            resource_type = path.parts[1].split('-', 1)[0]
            ids = by_name.get(f'{resource_type}/{path.stem}', [])
            if len(ids) != 1:
                raise SystemExit(
                    f'cannot resolve unique compiled XML ID for {rel}: '
                    f'{resource_type}/{path.stem} -> {ids}'
                )
            xml_id = ids[0]
        by_xml.setdefault(xml_id, []).append((line, attr, target))

    with zipfile.ZipFile(APK) as archive:
        checked = 0
        for xml_id, expected_attrs in sorted(by_xml.items()):
            entry = xml_files.get(xml_id)
            if not entry:
                raise SystemExit(f'compiled XML file missing for 0x{xml_id:08x}')
            attrs = xml_attributes(archive.read(entry))
            for line, attr, target in expected_attrs:
                matches = [
                    item
                    for item in attrs
                    if item['line'] == line and item['attr'] == attr
                ]
                if len(matches) != 1:
                    raise SystemExit(
                        f'0x{xml_id:08x}:{line} {attr}: expected one compiled attribute, got {matches}'
                    )
                item = matches[0]
                if item['type'] != 0x01 or item['data'] != target:
                    raise SystemExit(
                        f'0x{xml_id:08x}:{line} {attr}: compiled '
                        f'type/data=0x{item["type"]:02x}/0x{item["data"]:08x}, '
                        f'expected REFERENCE/0x{target:08x}'
                    )
                checked += 1
    if checked != 194:
        raise SystemExit(f'expected 194 compiled reference checks, completed {checked}')
    print(
        f'density split fusion verified: 114 fixed resource IDs, '
        f'194 restored XML references across {len(by_xml)} XML resources'
    )


if __name__ == '__main__':
    main()
