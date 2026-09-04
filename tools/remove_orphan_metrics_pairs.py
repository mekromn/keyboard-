#!/usr/bin/env python3
"""Delete metrics processor/helper pairs detached from every feature root."""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
PAIRS = {
    'evh': ('evi', 'LatinCountersMetricsProcessor'),
    'hcm': ('hcn', 'HmmMetricsProcessorHelper'),
    'hnh': ('hni', 'JarvisMetricsProcessor'),
    'hun': ('huo', 'LanguagePromoMetricsProcessorHelper'),
    'hzf': ('hzg', 'MigrationMetricsProcessor'),
    'ifu': ('ifv', 'NgaMetricsProcessor'),
    'igb': ('igc', 'RewriteMetricsProcessorHelper'),
    'igg': ('igh', 'SmartEditMetricsProcessor'),
    'jof': ('jog', 'SharingMetricsProcessor'),
    'jpn': ('jpo', 'SpellCheckerMetricsProcessorHelper'),
    'nev': ('new', 'EmojiKitchenBrowseMetricsProcessorHelper'),
    'ngd': ('nge', 'EmojiKitchenDataMetricsProcessor'),
    'nid': ('nie', 'ContentSuggestionMetricsProcessorHelper'),
    'nkk': ('nkl', 'ConversationIdMetricsProcessor'),
    'nny': ('nnz', 'DumpableMetricsProcessor'),
    'nwp': ('nwq', 'FeatureSplitMetricsProcessorHelper'),
    'onk': ('onl', 'InlineSuggestionMetricsProcessorHelper'),
    'plr': ('pls', 'MDDMetricsProcessor'),
    'psw': ('psx', 'StartupMetricsProcessor'),
    'qtf': ('qtg', 'StylusMetricsProcessorHelper'),
    'rdi': ('rdj', 'TouchOnNavigationMetricsProcessorHelper'),
    'roc': ('rod', 'UserFeatureCacheStatsMetricsProcessorHelper'),
    'rri': ('rrj', 'VoiceMetricsProcessor'),
}


def class_map():
    result = {}
    for path in ROOT.glob('smali*/**/*.smali'):
        text = path.read_text(errors='ignore')
        match = re.search(r'^\.class[^\n]* L([^;]+);', text, re.M)
        if match:
            result[match.group(1)] = (path, text)
    return result


classes = class_map()
remove = set(PAIRS)
remove.update(helper for helper, _ in PAIRS.values())

for processor, (helper, marker) in PAIRS.items():
    if processor not in classes or helper not in classes:
        raise SystemExit(f'{processor}/{helper}: missing class')
    processor_path, processor_text = classes[processor]
    helper_path, helper_text = classes[helper]
    if '.implements Lpqw;' not in processor_text:
        raise SystemExit(f'{processor}: not a metrics processor')
    if '.super Lpqh;' not in helper_text:
        raise SystemExit(f'{helper}: not a metrics helper')
    if marker not in processor_text + helper_text:
        raise SystemExit(f'{processor}/{helper}: marker {marker!r} missing')

    # Strict proof that the pair is no longer reachable from any feature class.
    for target, allowed in ((processor, {helper}), (helper, {processor})):
        needle = f'L{target};'
        inbound = sorted(
            name
            for name, (_, text) in classes.items()
            if name != target and needle in text
        )
        if set(inbound) != allowed:
            raise SystemExit(
                f'{target}: unexpected inbound refs {inbound}; '
                f'expected {sorted(allowed)}'
            )

before = sum(classes[name][0].stat().st_size for name in remove)
for name in sorted(remove):
    classes[name][0].unlink()
    print('deleted unreachable metrics class', name)

remaining = class_map()
for name in remove:
    needle = f'L{name};'
    hits = [owner for owner, (_, text) in remaining.items() if needle in text]
    if hits:
        raise SystemExit(f'{name}: residual descriptor refs {hits[:20]}')

print(
    f'physically removed {len(PAIRS)} orphan metrics pairs / '
    f'{len(remove)} classes / {before} smali bytes'
)
