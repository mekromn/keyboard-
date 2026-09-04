#!/usr/bin/env python3
"""Delete fully detached Writing Tools and Latin counters metric clusters."""
from pathlib import Path
import re

ROOT = Path('/mnt/data/meboard_work/buildtree')
CLUSTERS = {
    'writing_tools_training_cache': {
        'classes': {'hrs', 'hrt', 'hru'},
        'markers': {
            'WritingToolsTrainingCacheMetricsProcessor',
            'WritingToolsTrainingCacheMetricsProcessorProvider',
        },
    },
    'latin_common_counters': {
        'classes': {'hys', 'hyt', 'hyr'},
        'markers': {
            'LatinCommonCountersMetricsProcessor',
            'LatinCommonCountersMetricsProcessorHelper',
        },
    },
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
all_remove = set()
for label, spec in CLUSTERS.items():
    members = set(spec['classes'])
    all_remove |= members
    for name in members:
        if name not in classes:
            raise SystemExit(f'{label}: missing {name}')

    combined = '\n'.join(classes[name][1] for name in members)
    for marker in spec['markers']:
        if marker not in combined:
            raise SystemExit(f'{label}: missing marker {marker}')

    # A closed descriptor island cannot be constructed or invoked by feature code.
    for target in members:
        inbound = {
            owner
            for owner, (_, text) in classes.items()
            if owner != target and f'L{target};' in text
        }
        if not inbound <= members:
            raise SystemExit(
                f'{label}/{target}: external inbound '
                f'{sorted(inbound - members)}'
            )
    print(label, 'is a closed descriptor island:', sorted(members))

bytes_before = sum(classes[name][0].stat().st_size for name in all_remove)
for name in sorted(all_remove):
    classes[name][0].unlink()
    print('deleted', name)

remaining = class_map()
for name in all_remove:
    hits = [owner for owner, (_, text) in remaining.items() if f'L{name};' in text]
    if hits:
        raise SystemExit(f'{name}: residual refs {hits[:20]}')

print(
    f'removed {len(all_remove)} closed metrics classes / '
    f'{bytes_before} smali bytes'
)
