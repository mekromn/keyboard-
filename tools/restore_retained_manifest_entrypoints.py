#!/usr/bin/env python3
"""Verify retained Meboard component entry points survive Stage-1 privacy cuts.

These components are part of the retained feature contract, not passive telemetry:

* LocalComputationResultHandlingService — local/on-device computation results.
* ImageFeedbackActivity — explicit user-invoked image feedback.
* DecoderStateReportActivity — explicit decoder report UI.
* QualityBugReportActivity — explicit quality/bug report UI.

Stage 1 now preserves them directly from the pristine manifest. This gate refuses
missing/duplicate registrations or missing implementations, while requiring
federated example stores, debug UI, and multiprocess metrics registrations to
remain absent.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

WORK = Path('/mnt/data/meboard_work')
TARGET = WORK / 'buildtree/AndroidManifest.xml'
TREE = WORK / 'buildtree'
NEW = 'com.mekromn.meboard'
ANDROID = '{http://schemas.android.com/apk/res/android}'

RETAIN = (
    'LocalComputationResultHandlingService',
    'ImageFeedbackActivity',
    'DecoderStateReportActivity',
    'QualityBugReportActivity',
)

MUST_REMAIN_ABSENT = (
    'InAppJobService',
    'FeatureSplitDebugActivity',
    'FeatureSplitMultiprocessMetricsService',
    'SpeechPrecomputedFeatureExampleStoreService',
    'NWPSanityCheckEvalExampleStoreService',
)


def descriptor_exists(name: str) -> bool:
    if name.startswith('.'):
        name = NEW + name
    descriptor = 'L' + name.replace('.', '/') + ';'
    rx = re.compile(r'^\.class[^\n]* ' + re.escape(descriptor) + r'\s*$', re.M)
    for path in TREE.glob('smali*/**/*.smali'):
        try:
            head = path.read_text(errors='ignore')[:4096]
        except OSError:
            continue
        if rx.search(head):
            return True
    return False


def main() -> None:
    if not TARGET.is_file():
        raise SystemExit(f'missing target manifest: {TARGET}')

    tree = ET.parse(TARGET)
    root = tree.getroot()
    app = root.find('application')
    if app is None:
        raise SystemExit('application element missing')
    if root.get('package') != NEW:
        raise SystemExit(f'unexpected target package: {root.get("package")!r}')

    names = [e.get(ANDROID + 'name', '') for e in list(app)]
    retained: list[str] = []
    for suffix in RETAIN:
        matches = [name for name in names if suffix in name]
        if len(matches) != 1:
            raise SystemExit(f'retained component count {suffix}: {matches}')
        name = matches[0]
        if not descriptor_exists(name):
            raise SystemExit(f'retained component implementation missing: {name}')
        retained.append(name)

    for suffix in MUST_REMAIN_ABSENT:
        matches = [name for name in names if suffix in name]
        if matches:
            raise SystemExit(
                f'training/debug/reporting registration unexpectedly present: {matches}'
            )

    print('retained manifest entry points verified:', retained)


if __name__ == '__main__':
    main()
