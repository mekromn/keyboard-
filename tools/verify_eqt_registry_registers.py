#!/usr/bin/env python3
"""Reject invalid register state in Meboard's generated module registry.

The Gboard 18.0.3 ``eqt.aI()`` method is one large straight-line Dagger module
array builder. Some removed module blocks also contained integer initializers
reused by later retained factories. Smali assembles even when those initializers
are accidentally deleted, but ART rejects the class at startup with VerifyError.

This verifier intentionally runs on the decoded build tree before every APK
checkpoint. It checks all local-register reads in this straight-line method and
also pins the two reusable discriminator values whose loss caused the stage-16
startup crash.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')
EQT = ROOT / 'smali' / 'eqt.smali'
METHOD = '.method public final aI()Ljava/util/Set;'


def extract_method(text: str) -> list[str]:
    start = text.find(METHOD)
    if start < 0:
        raise SystemExit('eqt.aI() method not found')
    end = text.find('\n.end method', start)
    if end < 0:
        raise SystemExit('eqt.aI() method is unterminated')
    return text[start:end].splitlines()


def classify(line: str) -> tuple[list[str], list[str]]:
    """Return (uses, defs) for the opcode subset present in eqt.aI()."""
    stripped = line.strip()
    registers = re.findall(r'\b[vp]\d+\b', stripped)
    if not registers:
        return [], []
    op = stripped.split()[0]

    if op.startswith('move-result'):
        return [], [registers[0]]
    if op.startswith('move'):
        if len(registers) != 2:
            raise SystemExit(f'unexpected move shape: {stripped}')
        return [registers[1]], [registers[0]]
    if op.startswith('const') or op == 'new-instance':
        return [], [registers[0]]
    if op == 'new-array':
        if len(registers) < 2:
            raise SystemExit(f'unexpected new-array shape: {stripped}')
        return [registers[1]], [registers[0]]
    if op.startswith('iget'):
        return registers[1:], [registers[0]]
    if op.startswith('sget'):
        return [], [registers[0]]
    if op.startswith(('invoke-', 'filled-new-array')):
        return registers, []
    if op.startswith('aput'):
        return registers, []
    if op.startswith('return'):
        return registers, []

    raise SystemExit(f'unhandled register-using opcode in eqt.aI(): {stripped}')


def main() -> None:
    if not EQT.is_file():
        raise SystemExit(f'missing generated component: {EQT}')

    lines = extract_method(EQT.read_text())
    body = '\n'.join(lines)
    if '    .locals 24' not in body:
        raise SystemExit('eqt.aI() must reserve v23 for compacted array indices')

    required = {
        'v13': 'const/4 v13, 0x0',
        'v17': 'const/16 v17, 0xf',
    }
    for register, initializer in required.items():
        hits = [i for i, line in enumerate(lines) if line.strip() == initializer]
        if len(hits) != 1:
            raise SystemExit(
                f'{register}: expected exactly one reusable initializer '
                f'"{initializer}", found {len(hits)}'
            )

    defined: set[str] = set()
    errors: list[str] = []
    first_read: dict[str, int] = {}
    first_def: dict[str, int] = {}

    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(('.', ':', '#')):
            continue
        uses, defs = classify(stripped)
        for register in uses:
            if register.startswith('p'):
                continue
            first_read.setdefault(register, line_number)
            if register not in defined:
                errors.append(
                    f'line {line_number}: {register} read before definition: '
                    f'{stripped}'
                )
        for register in defs:
            if register.startswith('v'):
                first_def.setdefault(register, line_number)
                defined.add(register)

    for register in required:
        if first_read.get(register, 10**9) < first_def.get(register, 10**9):
            errors.append(
                f'{register}: first read at line {first_read[register]} precedes '
                f'first definition at line {first_def.get(register)}'
            )

    if errors:
        raise SystemExit('eqt.aI() register verification failed:\n  ' + '\n  '.join(errors))

    expected = {f'v{i}' for i in range(24)}
    missing = sorted(expected - defined, key=lambda item: int(item[1:]))
    if missing:
        raise SystemExit(f'eqt.aI() never defines expected locals: {missing}')

    print(
        'eqt.aI() register state verified: v0-v23 initialized before use; '
        'v13=0 and v17=15 preserved'
    )


if __name__ == '__main__':
    main()
