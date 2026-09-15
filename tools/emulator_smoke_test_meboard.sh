#!/usr/bin/env bash
set -euo pipefail

PKG="com.mekromn.meboard"
IME="$PKG/com.android.inputmethod.latin.LatinIME"
LAUNCHER="$PKG/com.google.android.libraries.inputmethod.launcher.LauncherActivity"
ADB="${ADB:-adb}"
APK="${1:-}"

if [[ -z "$APK" || ! -f "$APK" ]]; then
  echo "usage: $0 /path/to/Meboard.apk" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

adb_shell() { "$ADB" shell "$@"; }

echo "[1/9] waiting for Android device"
"$ADB" wait-for-device
until [[ "$(adb_shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do sleep 1; done

echo "[2/9] installing candidate"
"$ADB" install -r -t "$APK" >/dev/null

echo "[3/9] enabling/selecting Meboard IME"
adb_shell ime enable "$IME" >/dev/null
adb_shell ime set "$IME" >/dev/null

"$ADB" logcat -c
adb_shell am force-stop "$PKG" || true

echo "[4/9] launching Meboard settings"
adb_shell am start -W -n "$LAUNCHER" >"$TMP/am-start.txt"

dump_ui() {
  adb_shell uiautomator dump /sdcard/meboard-smoke.xml >/dev/null 2>&1 || true
  "$ADB" exec-out cat /sdcard/meboard-smoke.xml 2>/dev/null >"$TMP/window.xml" || true
}

node_center() {
  local query="$1"
  python3 - "$TMP/window.xml" "$query" <<'PY'
import re, sys, xml.etree.ElementTree as ET
p,q=sys.argv[1],sys.argv[2]
try: root=ET.parse(p).getroot()
except Exception: sys.exit(1)
for n in root.iter('node'):
    if n.attrib.get('text')==q or n.attrib.get('content-desc')==q:
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', n.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            print((x1+x2)//2,(y1+y2)//2)
            sys.exit(0)
sys.exit(1)
PY
}

wait_for_text() {
  local query="$1"; local timeout="${2:-15}"; local i
  for ((i=0;i<timeout*2;i++)); do
    dump_ui
    if node_center "$query" >/dev/null 2>&1; then return 0; fi
    sleep 0.5
  done
  return 1
}

echo "[5/9] opening Test Meboard"
if ! wait_for_text "Test Meboard" 20; then
  echo "FAIL: Test Meboard preference never appeared" >&2
  cat "$TMP/window.xml" >&2 || true
  exit 10
fi
read -r TX TY < <(node_center "Test Meboard")
adb_shell input tap "$TX" "$TY"

if ! wait_for_text "Close" 10; then
  echo "FAIL: Test Meboard dialog did not appear" >&2
  exit 11
fi

dump_ui
read -r EX EY < <(python3 - "$TMP/window.xml" <<'PY'
import re,sys,xml.etree.ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
for n in root.iter('node'):
    if n.attrib.get('class')=='android.widget.EditText':
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', n.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            print((x1+x2)//2,(y1+y2)//2)
            sys.exit(0)
sys.exit(1)
PY
) || { echo "FAIL: Test Meboard EditText missing" >&2; exit 12; }
adb_shell input tap "$EX" "$EY"
sleep 1

adb_shell input text MeboardSmoke >/dev/null || true
sleep 1

echo "[6/9] checking IME/process state"
IMEDUMP="$(adb_shell dumpsys input_method 2>/dev/null || true)"
if ! grep -Fq "$IME" <<<"$IMEDUMP"; then
  echo "FAIL: Meboard is not the active/current IME" >&2
  exit 20
fi
PID="$(adb_shell pidof "$PKG" 2>/dev/null | tr -d '\r' || true)"
if [[ -z "$PID" ]]; then
  echo "FAIL: Meboard process died while showing keyboard" >&2
  exit 21
fi

if ! grep -Eq 'mInputShown=true|mImeWindowVis=.*VISIBLE|mImeWindowVis=[^0]*1|inputShown=true' <<<"$IMEDUMP"; then
  W="$(adb_shell dumpsys window windows 2>/dev/null || true)"
  if ! grep -Eiq 'InputMethod|ImeWindow|input method' <<<"$W"; then
    echo "FAIL: no evidence of a shown IME window" >&2
    exit 22
  fi
fi

echo "[7/9] scanning logcat for ART/verifier/crash failures"
"$ADB" logcat -d -v threadtime >"$TMP/logcat.txt"
if grep -Ei 'VerifyError|Verifier rejected|FATAL EXCEPTION.*(LatinIME|Meboard)|Process: com\.mekromn\.meboard|am_crash.*com\.mekromn\.meboard' "$TMP/logcat.txt" >"$TMP/fatal.txt"; then
  echo "FAIL: runtime/verifier crash detected" >&2
  cat "$TMP/fatal.txt" >&2
  exit 30
fi

echo "[8/9] confirming Test Meboard remains interactive"
dump_ui
if ! grep -q 'class="android.widget.EditText"' "$TMP/window.xml"; then
  echo "FAIL: test editor disappeared after IME show" >&2
  exit 31
fi

echo "[9/9] PASS: Meboard installed, Test Meboard opened, editor focused, IME shown, process alive, no verifier/fatal crash"
