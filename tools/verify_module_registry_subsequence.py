#!/usr/bin/env python3
"""Verify that the compacted Meboard module registry preserves original factories.

Gboard's generated ``eqt.aI()`` method is a straight-line array builder. Removing
one factory block can accidentally remove a constant that is reused by the next
factory. Smali still assembles, but the next factory receives a stale synthetic
discriminator and may resolve to a duplicate module key at runtime.

Every retained Meboard factory must therefore be an exact ordered subsequence of
the original Gboard registry, including constructor descriptor and all resolved
constant constructor arguments. Reference arguments are normalized by type so
array/object temporaries do not depend on register numbering.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

WORK = Path('/mnt/data/meboard_work')
ORIGINAL = WORK / 'original_eqt.smali'
CURRENT = WORK / 'buildtree' / 'smali' / 'eqt.smali'
METHOD = '.method public final aI()Ljava/util/Set;'

Value = tuple[Any, ...]
Signature = tuple[str, str | None, tuple[Value, ...]]


def method_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise SystemExit(f'missing module registry: {path}')
    text = path.read_text()
    start = text.find(METHOD)
    if start < 0:
        raise SystemExit(f'{path}: eqt.aI() not found')
    end = text.find('\n.end method', start)
    if end < 0:
        raise SystemExit(f'{path}: unterminated eqt.aI()')
    return text[start:end].splitlines()


def entries(path: Path) -> list[Signature]:
    values: dict[str, Value] = {}
    objects: dict[str, dict[str, Any]] = {}
    result: list[Signature] = []

    def value(register: str) -> Value:
        return values.get(register, ('REF',))

    for line_number, line in enumerate(method_lines(path), 1):
        stripped = line.strip()

        match = re.match(
            r'const(?:/4|/16|/high16)?\s+([vp]\d+),\s+'
            r'(-?0x[0-9a-fA-F]+|-?\d+)', stripped,
        )
        if match:
            values[match.group(1)] = ('INT', int(match.group(2), 0))
            continue

        match = re.match(r'const-string(?:/jumbo)?\s+([vp]\d+),\s+"(.*)"', stripped)
        if match:
            values[match.group(1)] = ('STRING', match.group(2))
            continue

        match = re.match(r'const-class\s+([vp]\d+),\s+L([^;]+);', stripped)
        if match:
            values[match.group(1)] = ('CLASS', match.group(2))
            continue

        match = re.match(r'move(?:/from16|/16)?\s+([vp]\d+),\s+([vp]\d+)', stripped)
        if match:
            values[match.group(1)] = value(match.group(2))
            continue

        match = re.match(r'new-instance\s+([vp]\d+),\s+L([^;]+);', stripped)
        if match:
            register, class_name = match.groups()
            objects[register] = {
                'class': class_name,
                'descriptor': None,
                'arguments': (),
                'line': line_number,
            }
            values[register] = ('OBJECT', class_name)
            continue

        match = re.match(
            r'invoke-direct(?:/range)?\s+\{([^}]*)\},\s+'
            r'L([^;]+);-><init>\(([^)]*)\)V', stripped,
        )
        if match:
            registers = [item.strip() for item in match.group(1).split(',') if item.strip()]
            class_name, descriptor = match.group(2), match.group(3)
            if registers:
                receiver = registers[0]
                obj = objects.get(receiver)
                if obj and obj['class'] == class_name:
                    obj['descriptor'] = descriptor
                    obj['arguments'] = tuple(value(reg) for reg in registers[1:])
            continue

        match = re.match(r'aput-object\s+([vp]\d+),\s+v11,\s+[vp]\d+', stripped)
        if match:
            register = match.group(1)
            obj = objects.get(register)
            if obj is None:
                raise SystemExit(
                    f'{path}: line {line_number}: stored object {register} '
                    'has no tracked new-instance'
                )
            result.append((obj['class'], obj['descriptor'], obj['arguments']))

    if not result:
        raise SystemExit(f'{path}: no module registry entries found')
    return result


def show(signature: Signature) -> str:
    class_name, descriptor, arguments = signature
    return f'{class_name}.<init>({descriptor or ""}) args={arguments}'


def main() -> None:
    original = entries(ORIGINAL)
    current = entries(CURRENT)

    if len(current) >= len(original):
        raise SystemExit(
            f'expected compacted registry, got original={len(original)} current={len(current)}'
        )

    original_cursor = 0
    matched_positions: list[int] = []
    for current_index, signature in enumerate(current):
        while original_cursor < len(original) and original[original_cursor] != signature:
            original_cursor += 1
        if original_cursor == len(original):
            nearby = '\n'.join(
                f'  original[{i}]: {show(original[i])}'
                for i in range(max(0, len(original) - 8), len(original))
            )
            raise SystemExit(
                'module-registry subsequence verification failed:\n'
                f'  current[{current_index}]: {show(signature)}\n'
                '  no matching later factory exists in the original registry\n'
                f'{nearby}'
            )
        matched_positions.append(original_cursor)
        original_cursor += 1

    original_ints: dict[tuple[str, str | None], set[int]] = {}
    for class_name, descriptor, arguments in original:
        key = (class_name, descriptor)
        for argument in arguments:
            if argument and argument[0] == 'INT':
                original_ints.setdefault(key, set()).add(int(argument[1]))
    for index, (class_name, descriptor, arguments) in enumerate(current):
        allowed = original_ints.get((class_name, descriptor), set())
        for argument in arguments:
            if argument and argument[0] == 'INT' and int(argument[1]) not in allowed:
                raise SystemExit(
                    f'current[{index}] {class_name}: synthetic discriminator '
                    f'{argument[1]} never occurred in original; allowed={sorted(allowed)}'
                )

    print(
        'module registry verified as exact ordered subsequence: '
        f'{len(current)} retained of {len(original)} original factories; '
        'constructor constants preserved'
    )


if __name__ == '__main__':
    main()
