#!/usr/bin/env bash
set -euo pipefail

PKG="com.mekromn.meboard"
IME="$PKG/com.android.inputmethod.latin.LatinIME"
LAUNCHER="$PKG/com.google.android.libraries.inputmethod.launcher.LauncherActivity"
ADB="${ADB:-adb}"
APK="${1:-}"

if ! command -v "$ADB" >/dev/null 2>&1; then
  echo "FAIL: adb is not installed or not on PATH" >&2
  exit 3
fi
if [[ -z "$APK" || ! -f "$APK" ]]; then
  echo "usage: $0 /path/to/Meboard.apk" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
adb_shell() { "$ADB" shell "$@"; }

echo "[1/10] waiting for Android device"
"$ADB" wait-for-device
until [[ "$(adb_shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do sleep 1; done

echo "[2/10] installing candidate"
"$ADB" install -r -t "$APK" >"$TMP/install.txt"

echo "[3/10] enabling/selecting Meboard IME"
adb_shell ime enable "$IME" >/dev/null
adb_shell ime set "$IME" >/dev/null
"$ADB" logcat -c
adb_shell am force-stop "$PKG" || true

echo "[4/10] launching Meboard settings"
adb_shell am start -W -n "$LAUNCHER" >"$TMP/am-start.txt"

dump_ui() {
  adb_shell uiautomator dump /sdcard/meboard-smoke.xml >/dev/null 2>&1 || true
  "$ADB" exec-out cat /sdcard/meboard-smoke.xml 2>/dev/null >"$TMP/window.xml" || true
}
node_center() {
  local query="$1"
  python3 - "$TMP/window.xml" "$query" <<'PY'
import re,sys,xml.etree.ElementTree as ET
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

echo "[5/10] checking Test Meboard + clipboard-timeout settings"
wait_for_text "Test Meboard" 20 || { echo "FAIL: Test Meboard preference missing" >&2; exit 10; }
wait_for_text "Clipboard history timeout" 10 || { echo "FAIL: clipboard timeout preference missing" >&2; exit 11; }

read -r TX TY < <(node_center "Test Meboard")
adb_shell input tap "$TX" "$TY"
wait_for_text "Close" 10 || { echo "FAIL: Test Meboard dialog did not appear" >&2; exit 12; }
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
) || { echo "FAIL: Test Meboard EditText missing" >&2; exit 13; }
adb_shell input tap "$EX" "$EY"
sleep 2

echo "[6/10] checking process survived keyboard show"
PID="$(adb_shell pidof "$PKG" 2>/dev/null | tr -d '\r' || true)"
[[ -n "$PID" ]] || { echo "FAIL: Meboard process died when keyboard was shown" >&2; exit 20; }

echo "[7/10] checking Meboard is current/shown IME"
IMEDUMP="$(adb_shell dumpsys input_method 2>/dev/null || true)"
grep -Fq "$IME" <<<"$IMEDUMP" || { echo "FAIL: Meboard not current IME" >&2; exit 21; }
if ! grep -Eq 'mInputShown=true|mImeWindowVis=.*VISIBLE|mImeWindowVis=[^0]*1|inputShown=true' <<<"$IMEDUMP"; then
  W="$(adb_shell dumpsys window windows 2>/dev/null || true)"
  grep -Eiq 'InputMethod|ImeWindow|input method' <<<"$W" || { echo "FAIL: no shown IME-window evidence" >&2; exit 22; }
fi

echo "[8/10] checking editor interaction"
adb_shell input text MeboardSmoke >/dev/null || true
sleep 1
dump_ui
grep -q 'class="android.widget.EditText"' "$TMP/window.xml" || { echo "FAIL: editor disappeared" >&2; exit 23; }

echo "[9/10] scanning logcat for verifier/fatal crash"
"$ADB" logcat -d -v threadtime >"$TMP/logcat.txt"
if grep -Ei 'VerifyError|Verifier rejected|FATAL EXCEPTION.*(LatinIME|Meboard)|Process: com\.mekromn\.meboard|am_crash.*com\.mekromn\.meboard' "$TMP/logcat.txt" >"$TMP/fatal.txt"; then
  echo "FAIL: runtime/verifier crash detected" >&2
  cat "$TMP/fatal.txt" >&2
  exit 30
fi

echo "[10/10] PASS: install + settings + Test Meboard + keyboard render + process + logcat gates"
