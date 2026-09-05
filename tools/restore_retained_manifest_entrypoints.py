#!/usr/bin/env python3
"""Restore retained Meboard component entry points after Stage-16 privacy cuts.

The first physical-removal pass removed several manifest registrations by broad
name classification. Four implementations remain intact and belong to the
retained contract rather than passive telemetry:

* LocalComputationResultHandlingService — local/on-device computation results.
* ImageFeedbackActivity — explicit user-invoked image feedback.
* DecoderStateReportActivity — explicit decoder report UI.
* QualityBugReportActivity — explicit quality/bug report UI.

This pass copies only their original manifest elements, rebases package-bound
attribute values to Meboard, and refuses duplicates or missing implementations.
Federated/background-training example stores, debug UI, and multiprocess metrics
registrations remain absent.
"""
from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from pathlib import Path

WORK = Path('/mnt/data/meboard_work')
ORIGINAL = WORK / 'decoded/base/AndroidManifest.xml'
TARGET = WORK / 'buildtree/AndroidManifest.xml'
TREE = WORK / 'buildtree'
OLD = 'com.google.android.inputmethod.latin'
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
    for path in TREE.glob('smali*/**/*.smali'):
        try:
            head = path.read_text(errors='ignore')[:2048]
        except OSError:
            continue
        if re.search(r'^\.class[^\n]* ' + re.escape(descriptor) + r'\s*$', head, re.M):
            return True
    return False


def main() -> None:
    for path in (ORIGINAL, TARGET):
        if not path.is_file():
            raise SystemExit(f'missing manifest input: {path}')

    ET.register_namespace('android', 'http://schemas.android.com/apk/res/android')
    original_tree = ET.parse(ORIGINAL)
    target_tree = ET.parse(TARGET)
    original_app = original_tree.getroot().find('application')
    target_app = target_tree.getroot().find('application')
    if original_app is None or target_app is None:
        raise SystemExit('application element missing')

    originals: dict[str, ET.Element] = {}
    for element in list(original_app):
        name = element.get(ANDROID + 'name', '')
        for suffix in RETAIN:
            if suffix in name:
                if suffix in originals:
                    raise SystemExit(f'ambiguous original component: {suffix}')
                originals[suffix] = element

    missing = [suffix for suffix in RETAIN if suffix not in originals]
    if missing:
        raise SystemExit(f'original retained components missing: {missing}')

    existing_names = [e.get(ANDROID + 'name', '') for e in list(target_app)]
    restored: list[str] = []
    for suffix in RETAIN:
        matches = [name for name in existing_names if suffix in name]
        if len(matches) > 1:
            raise SystemExit(f'duplicate target component before restore: {suffix}: {matches}')
        if not matches:
            element = copy.deepcopy(originals[suffix])
            for node in element.iter():
                for key, value in list(node.attrib.items()):
                    node.set(key, value.replace(OLD, NEW))
            target_app.append(element)
            restored.append(element.get(ANDROID + 'name', suffix))

    final_names = [e.get(ANDROID + 'name', '') for e in list(target_app)]
    for suffix in RETAIN:
        matches = [name for name in final_names if suffix in name]
        if len(matches) != 1:
            raise SystemExit(f'retained component count {suffix}: {matches}')
        if not descriptor_exists(matches[0]):
            raise SystemExit(f'retained component implementation missing: {matches[0]}')

    for suffix in MUST_REMAIN_ABSENT:
        matches = [name for name in final_names if suffix in name]
        if matches:
            raise SystemExit(f'training/debug/reporting registration unexpectedly present: {matches}')

    target_tree.write(TARGET, encoding='utf-8', xml_declaration=True)
    print('restored retained manifest entry points:', restored or 'already present')


if __name__ == '__main__':
    main()
