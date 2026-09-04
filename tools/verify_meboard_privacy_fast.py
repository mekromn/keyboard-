#!/usr/bin/env python3
"""Fast static acceptance gate for the Meboard privacy rebuild.

This verifier distinguishes executable/registered privacy failures from harmless
historical strings. It scans every decoded text source once, reports exact
locations, and exits non-zero when a removed account, telemetry, remote-config,
or federated-training path is reintroduced.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

FATAL = {
    "android_account_manager_get": re.compile(r"Landroid/accounts/AccountManager;->get\("),
    "android_account_manager_list": re.compile(r"Landroid/accounts/AccountManager;->getAccounts\(\)"),
    "gms_get_accounts": re.compile(r"(?:const-string\s+\w+,\s+\"get_accounts\"|com\.google\.android\.gms\.auth\.accounts)"),
    "get_accounts_permission": re.compile(r"android\.permission\.GET_ACCOUNTS"),
    "account_status_module": re.compile(r"(?:Lmph;|AccountsStatusCheckerModule|AccountsCapabilitiesChangedReceiver)"),
    "native_federated_runner": re.compile(r"(?:NativeFLRunnerWrapper|runFlTraining|DynamicTrainer|FederatedResultHandlingService)"),
    "brella_federated_service": re.compile(r"(?:InAppTrainingService|ExampleStoreServiceMultiplexer|LocalComputationResultHandlingService)"),
    "clearcut_transport": re.compile(r"(?:ClearcutMetricTransmitter|LegacyClearcutAdapter|BaseClearcutAdapter|LogEventParcelable|com/google/android/gms/clearcut/internal)"),
    "primes_runtime": re.compile(r"(?:com/google/android/libraries/performance/primes|recordNetworkMetricsToPrimes|PrimesApi|PrimesProvider)"),
    "remote_phenotype_registration": re.compile(r"(?:PhenotypeUpdateBackgroundBroadcastReceiver|AccountRemovedBroadcastReceiver|phenotype\.registration|Fetch and update phenotype flags)"),
    "cronet_telemetry_opt_in": re.compile(r"android\.net\.http\.EnableTelemetry"),
    "keyhound_collector": re.compile(r"(?:Keyhound|keyhound|encrypted.*input.*dump)"),
}

MANIFEST_COMPONENT_MARKERS = re.compile(
    r"(?:MetricsService|DiagnosticsReceiver|LifeboatReceiver|ColdStartupTraceContentProvider|"
    r"FeatureSplitMultiprocessMetricsService|FederatedResultHandlingService|InAppTrainingService|"
    r"AccountsCapabilitiesChangedReceiver|PhenotypeUpdateBackgroundBroadcastReceiver)"
)

REPORT_ONLY = {
    "telemetry_word": re.compile(r"telemetry", re.I),
    "clearcut_word": re.compile(r"clearcut", re.I),
    "primes_word": re.compile(r"\bprimes\b", re.I),
    "federated_word": re.compile(r"federat", re.I),
    "metric_word": re.compile(r"metric", re.I),
    "phenotype_word": re.compile(r"phenotype", re.I),
}

TEXT_SUFFIXES = {".smali", ".xml", ".json", ".txt", ".properties", ".yml", ".yaml", ".cfg"}


def scan(root: Path) -> dict:
    fatal = defaultdict(list)
    report = defaultdict(list)
    files_scanned = 0
    lines_scanned = 0

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if "build" in path.relative_to(root).parts:
            continue
        files_scanned += 1
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        for number, line in enumerate(text.splitlines(), 1):
            lines_scanned += 1
            for name, rx in FATAL.items():
                if rx.search(line):
                    fatal[name].append({"file": rel, "line": number, "text": line.strip()[:500]})
            for name, rx in REPORT_ONLY.items():
                if rx.search(line) and len(report[name]) < 250:
                    report[name].append({"file": rel, "line": number, "text": line.strip()[:500]})

    manifest = root / "AndroidManifest.xml"
    package = None
    if manifest.is_file():
        mtext = manifest.read_text(errors="replace")
        match = re.search(r"\bpackage=\"([^\"]+)\"", mtext)
        package = match.group(1) if match else None
        if package != "com.mekromn.meboard":
            fatal["wrong_package_identity"].append({"file": "AndroidManifest.xml", "line": 1, "text": repr(package)})
        for match in MANIFEST_COMPONENT_MARKERS.finditer(mtext):
            fatal["registered_telemetry_component"].append(
                {"file": "AndroidManifest.xml", "line": mtext.count("\n", 0, match.start()) + 1, "text": match.group(0)}
            )
    else:
        fatal["missing_manifest"].append({"file": "AndroidManifest.xml", "line": 0, "text": "missing"})

    return {
        "root": str(root),
        "package": package,
        "files_scanned": files_scanned,
        "lines_scanned": lines_scanned,
        "fatal": dict(fatal),
        "report_only": dict(report),
        "passed": not fatal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?", default=Path("/mnt/data/meboard_work/buildtree"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    if not args.root.is_dir():
        raise SystemExit(f"decoded tree does not exist: {args.root}")
    result = scan(args.root)
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.json:
        args.json.write_text(encoded + "\n")
    print(encoded)
    if not result["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
