#!/usr/bin/env python3
"""Physically remove Gboard's hard-coded APK certificate whitelist.

Meboard is intentionally signed with its own stable certificate. The upstream
LatinApp schedules a shared Runnable that compares the installed package signer
against hard-coded Google certificate digests and throws IllegalStateException
for every legitimate independently signed fork. This pass removes the producer,
the shared synthetic branch, the comparator, and the embedded whitelist bytes.
The application-context producer is retained because later startup code reuses
that register as a real ``Context``. Android Package Manager signature/update
enforcement remains untouched.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')


def method_span(text: str, header_regex: str, desc: str) -> tuple[int, int, str]:
    match = re.search(
        rf'(?ms)^\.method[^\n]*{header_regex}\n.*?^\.end method\n?',
        text,
    )
    if not match:
        raise SystemExit(f'{desc}: method not found')
    return match.start(), match.end(), match.group(0)


# Remove the sole Runnable discriminator-8 producer from LatinApp startup.
latin = ROOT / 'smali/com/google/android/apps/inputmethod/latin/LatinApp.smali'
lines = latin.read_text().splitlines()
hits = [i for i, line in enumerate(lines) if line.strip() == 'const/16 v3, 0x8']
if len(hits) != 1:
    raise SystemExit(
        f'LatinApp signature-check discriminator: expected one hit, got {hits}'
    )
mid = hits[0]
start = next(
    (
        i
        for i in range(mid, max(-1, mid - 30), -1)
        if 'LatinApp;->getApplicationContext()Landroid/content/Context;'
        in lines[i]
    ),
    None,
)
end = next(
    (
        i
        for i in range(mid, min(len(lines), mid + 30))
        if 'Ljava/util/concurrent/Executor;->execute(Ljava/lang/Runnable;)V'
        in lines[i]
    ),
    None,
)
if start is None or end is None:
    raise SystemExit('LatinApp signature-check scheduling block bounds not found')
block = '\n'.join(lines[start : end + 1])
for required in (
    'new-instance v2, Lmm;',
    'invoke-direct {v2, v7, v3}, Lmm;-><init>(Ljava/lang/Object;I)V',
    'const/16 v3, 0x8',
):
    if required not in block:
        raise SystemExit(f'LatinApp signature-check block missing {required}')

# The guard's scheduling block also initializes v7 with the application Context.
# A later retained startup path calls qhy.I(v7). Deleting that shared producer
# leaves v7 holding an unrelated Object and ART rejects LatinApp.e() before
# Application.onCreate. Preserve only the Context producer; delete the executor,
# Runnable construction, discriminator, and scheduling call.
move_result = next(
    (
        i
        for i in range(start + 1, mid)
        if lines[i].strip() == 'move-result-object v7'
    ),
    None,
)
if move_result is None:
    raise SystemExit('LatinApp shared application-context move-result not found')
producer = '\n'.join(lines[start : move_result + 1])
if (
    'LatinApp;->getApplicationContext()Landroid/content/Context;' not in producer
    or 'move-result-object v7' not in producer
):
    raise SystemExit('LatinApp application-context producer is not the expected sequence')
del lines[move_result + 1 : end + 1]
latin_text = '\n'.join(lines) + '\n'
producer_pattern = re.compile(
    r'invoke-virtual \{v0\}, '
    r'Lcom/google/android/apps/inputmethod/latin/LatinApp;'
    r'->getApplicationContext\(\)Landroid/content/Context;'
    r'\s+move-result-object v7'
)
if len(producer_pattern.findall(latin_text)) != 1:
    raise SystemExit('LatinApp must retain exactly one shared v7 Context producer')
for forbidden in (
    'const/16 v3, 0x8',
    'new-instance v2, Lmm;',
    'invoke-direct {v2, v7, v3}, Lmm;-><init>(Ljava/lang/Object;I)V',
):
    if forbidden in latin_text:
        raise SystemExit(f'LatinApp signature scheduling residue remains: {forbidden}')
consumer = 'invoke-static {v7}, Lqhy;->I(Landroid/content/Context;)Lqhy;'
producer_match = producer_pattern.search(latin_text)
consumer_pos = latin_text.find(consumer)
if producer_match is None or consumer_pos < producer_match.end():
    raise SystemExit('LatinApp retained Context consumer is not dominated by its producer')
latin.write_text(latin_text)
print('LatinApp: removed signature-whitelist scheduling while preserving shared Context producer')

# Remove discriminator-8 code from the shared Runnable. Its now-impossible
# switch slot targets the common return label, leaving no dead verifier branch.
mm = ROOT / 'smali/mm.smali'
text = mm.read_text()
a, b, body = method_span(text, r'run\(\)V', 'mm.run')
branch_start = body.find('\n    :pswitch_b\n')
branch_end = body.find('\n    :pswitch_c\n', branch_start + 1)
if branch_start < 0 or branch_end < 0:
    raise SystemExit('mm.run signature branch boundaries not found')
branch = body[branch_start:branch_end]
for required in (
    'Lrpv;->a(Landroid/content/Context;Ljava/lang/String;)Z',
    'APK is signed by unrecognized certificates:',
    'Ljava/lang/IllegalStateException;',
):
    if required not in branch:
        raise SystemExit(f'mm signature branch missing {required}')
body = body[:branch_start] + body[branch_end:]
data_pos = body.rfind('\n    :pswitch_data_0\n')
if data_pos < 0:
    raise SystemExit('mm.run packed-switch data not found')
head, data = body[:data_pos], body[data_pos:]
data, changed = re.subn(
    r'(?m)^(\s*):pswitch_b\s*$', r'\1:cond_15', data, count=1
)
if changed != 1:
    raise SystemExit(
        f'mm.run expected one discriminator-8 table entry, rewrote {changed}'
    )
body = head + data
for forbidden in (
    ':pswitch_b',
    'APK is signed by unrecognized certificates:',
    'Lrpv;->a(Landroid/content/Context;Ljava/lang/String;)Z',
):
    if forbidden in body:
        raise SystemExit(f'mm.run still contains signature guard marker {forbidden}')
mm.write_text(text[:a] + body + text[b:])
print('mm.run: removed signature-whitelist branch and switch target')

# Remove the comparator and four embedded recognized-certificate digests while
# retaining generic digest helpers used by the diagnostic dumper.
rpv = ROOT / 'smali/rpv.smali'
text = rpv.read_text()
for field in ('a', 'c', 'd', 'e'):
    text, changed = re.subn(
        rf'(?m)^\.field (?:public|private) static final {field}:\[B\n\n?',
        '',
        text,
        count=1,
    )
    if changed != 1:
        raise SystemExit(f'rpv whitelist field {field}: removed {changed}')

ca, cb, _ = method_span(text, r'static constructor <clinit>\(\)V', 'rpv.<clinit>')
minimal_clinit = '''.method static constructor <clinit>()V
    .locals 1

    const-string v0, "com/google/android/libraries/inputmethod/utils/SignatureUtils"

    invoke-static {v0}, Lwef;->i(Ljava/lang/String;)Lwef;

    move-result-object v0

    sput-object v0, Lrpv;->b:Lwef;

    return-void
.end method

'''
text = text[:ca] + minimal_clinit + text[cb:]
ma, mb, comparator = method_span(
    text,
    r'public static a\(Landroid/content/Context;Ljava/lang/String;\)Z',
    'rpv whitelist comparator',
)
if 'Ljava/util/Arrays;->equals' not in comparator:
    raise SystemExit('rpv.a does not contain expected certificate comparison')
text = text[:ma] + text[mb:]
for forbidden in (
    '.field public static final a:[B',
    '.field private static final c:[B',
    '.field private static final d:[B',
    '.field private static final e:[B',
    '.method public static a(Landroid/content/Context;Ljava/lang/String;)Z',
    '.array-data 1',
):
    if forbidden in text:
        raise SystemExit(f'rpv still contains whitelist marker {forbidden}')
rpv.write_text(text)
print('rpv: deleted whitelist comparator and embedded certificate digests')

for needle in (
    'APK is signed by unrecognized certificates:',
    'Lrpv;->a(Landroid/content/Context;Ljava/lang/String;)Z',
):
    residual = [
        str(path.relative_to(ROOT))
        for path in ROOT.glob('smali*/**/*.smali')
        if needle in path.read_text(errors='ignore')
    ]
    if residual:
        raise SystemExit(
            f'residual signature-whitelist implementation {needle}: {residual}'
        )

print('certificate whitelist enforcement physically removed; Android signature security retained')
