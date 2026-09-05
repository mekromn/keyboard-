#!/usr/bin/env python3
"""Verify the shared LatinApp.e() application-context register contract.

The upstream certificate-whitelist scheduler initializes v7 with the application
Context before constructing its Runnable. Meboard removes the scheduler, but a
later retained startup path still passes v7 to qhy.I(Context). The producer must
therefore remain even though all certificate-check scheduling code is deleted.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/mnt/data/meboard_work/buildtree')
PATH = ROOT / 'smali/com/google/android/apps/inputmethod/latin/LatinApp.smali'
METHOD = '.method protected final e()V'

if not PATH.is_file():
    raise SystemExit(f'missing LatinApp smali: {PATH}')
text = PATH.read_text()
start = text.find(METHOD)
if start < 0:
    raise SystemExit('LatinApp.e() not found')
end = text.find('\n.end method', start)
if end < 0:
    raise SystemExit('LatinApp.e() is unterminated')
body = text[start:end]

producer_rx = re.compile(
    r'invoke-virtual \{v0\}, '
    r'Lcom/google/android/apps/inputmethod/latin/LatinApp;'
    r'->getApplicationContext\(\)Landroid/content/Context;'
    r'\s+move-result-object v7'
)
producers = list(producer_rx.finditer(body))
if len(producers) != 1:
    raise SystemExit(f'expected exactly one v7 application-Context producer, found {len(producers)}')
consumer = 'invoke-static {v7}, Lqhy;->I(Landroid/content/Context;)Lqhy;'
consumer_pos = body.find(consumer)
if consumer_pos < 0:
    raise SystemExit('retained qhy.I(v7 Context) consumer is missing')
if consumer_pos <= producers[0].end():
    raise SystemExit('v7 Context consumer is not dominated by the retained producer')

between = body[producers[0].end():consumer_pos]
writer_rx = re.compile(
    r'(?m)^\s*(?:'
    r'move(?:-object|-wide)?(?:/from16|/16)?|move-result(?:-object|-wide)?|'
    r'const(?:/4|/16|/high16|-string(?:/jumbo)?|-class|-wide(?:/16|/32|/high16)?)?|'
    r'new-instance|new-array|array-length|instance-of|check-cast|'
    r'[ais]get(?:-object|-wide|-boolean|-byte|-char|-short)?|'
    r'cmp(?:g|l)?-(?:float|double)|cmp-long|'
    r'neg-(?:int|long|float|double)|not-(?:int|long)|'
    r'(?:int|long|float|double|byte|char|short)-to-(?:int|long|float|double|byte|char|short)'
    r')\s+v7(?:,|\s|$)'
)
writers = [line.strip() for line in between.splitlines() if writer_rx.match(line)]
if writers:
    raise SystemExit(f'v7 is overwritten between Context producer and consumer: {writers}')

# LatinApp.e() has other legitimate executor scheduling for retained startup
# behavior. Reject only the exact signature-whitelist Runnable producer; a
# generic Executor.execute occurrence is not evidence that the removed guard
# survived.
for forbidden in (
    'const/16 v3, 0x8',
    'new-instance v2, Lmm;',
    'invoke-direct {v2, v7, v3}, Lmm;-><init>(Ljava/lang/Object;I)V',
):
    if forbidden in body:
        raise SystemExit(f'signature-whitelist scheduling residue remains in LatinApp.e(): {forbidden}')

print('LatinApp.e() v7 Context producer/consumer contract verified; signature scheduler absent')
