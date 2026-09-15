#!/usr/bin/env bash
set -euo pipefail
PKG="com.mekromn.meboard"
IME="$PKG/com.android.inputmethod.latin.LatinIME"
LAUNCHER="$PKG/com.google.android.libraries.inputmethod.launcher.LauncherActivity"
ADB="${ADB:-adb}"
APK="${1:-}"
if ! command -v "$ADB" >/dev/null 2>&1; then echo "FAIL: adb is not installed or not on PATH" >&2; exit 3; fi
if [[ -z "$APK" || ! -f "$APK" ]]; then echo "usage: $0 /path/to/Meboard.apk" >&2; exit 2; fi
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
adb_shell(){ "$ADB" shell "$@"; }
dump_ui(){ adb_shell uiautomator dump /sdcard/meboard-smoke.xml >/dev/null 2>&1 || true; "$ADB" exec-out cat /sdcard/meboard-smoke.xml 2>/dev/null >"$TMP/window.xml" || true; }
node_center(){ local q="$1"; python3 - "$TMP/window.xml" "$q" <<'PY'
import re,sys,xml.etree.ElementTree as ET
p,q=sys.argv[1:]
try: root=ET.parse(p).getroot()
except Exception: sys.exit(1)
for n in root.iter('node'):
    if n.attrib.get('text')==q or n.attrib.get('content-desc')==q:
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups()); print((x1+x2)//2,(y1+y2)//2); sys.exit(0)
sys.exit(1)
PY
}
wait_for_text(){ local q="$1" timeout="${2:-15}" i; for ((i=0;i<timeout*2;i++)); do dump_ui; node_center "$q" >/dev/null 2>&1 && return 0; sleep .5; done; return 1; }

echo '[1/13] wait for Android 16 device'
"$ADB" wait-for-device
until [[ "$(adb_shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == 1 ]]; do sleep 1; done

echo '[2/13] install/update candidate'
"$ADB" install -r -t "$APK" >"$TMP/install.txt"

echo '[3/13] enable/select Meboard'
adb_shell ime enable "$IME" >/dev/null; adb_shell ime set "$IME" >/dev/null
"$ADB" logcat -c; adb_shell am force-stop "$PKG" || true

echo '[4/13] launch root settings'
adb_shell am start -W -n "$LAUNCHER" >"$TMP/am-start.txt"
wait_for_text 'Test Meboard' 20 || { echo 'FAIL: Test Meboard missing' >&2; exit 10; }
dump_ui
if grep -q 'text="Clipboard history timeout"' "$TMP/window.xml"; then echo 'FAIL: clipboard timeout incorrectly present on root settings' >&2; exit 11; fi

echo '[5/13] run exact Test Meboard keyboard-show repro'
read -r x y < <(node_center 'Test Meboard'); adb_shell input tap "$x" "$y"
wait_for_text 'Close' 10 || { echo 'FAIL: Test Meboard dialog missing' >&2; exit 12; }
dump_ui
read -r ex ey < <(python3 - "$TMP/window.xml" <<'PY'
import re,sys,xml.etree.ElementTree as ET
root=ET.parse(sys.argv[1]).getroot()
for n in root.iter('node'):
    if n.attrib.get('class')=='android.widget.EditText':
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups()); print((x1+x2)//2,(y1+y2)//2); sys.exit(0)
sys.exit(1)
PY
) || { echo 'FAIL: Test Meboard EditText missing' >&2; exit 13; }
adb_shell input tap "$ex" "$ey"; sleep 2

echo '[6/13] assert keyboard/process survived'
[[ -n "$(adb_shell pidof "$PKG" 2>/dev/null | tr -d '\r')" ]] || { echo 'FAIL: process died on keyboard show' >&2; exit 20; }
IMEDUMP="$(adb_shell dumpsys input_method 2>/dev/null || true)"
grep -Fq "$IME" <<<"$IMEDUMP" || { echo 'FAIL: Meboard not current IME' >&2; exit 21; }
adb_shell input text MeboardSmoke >/dev/null || true; sleep 1

echo '[7/13] scan keyboard-show logcat'
"$ADB" logcat -d -v threadtime >"$TMP/logcat-keyboard.txt"
if grep -Ei 'VerifyError|Verifier rejected|FATAL EXCEPTION.*(LatinIME|Meboard)|Process: com\.mekromn\.meboard|am_crash.*com\.mekromn\.meboard' "$TMP/logcat-keyboard.txt" >"$TMP/fatal.txt"; then cat "$TMP/fatal.txt" >&2; exit 30; fi

echo '[8/13] return to root settings and enter Clipboard submenu'
adb_shell input keyevent 4; sleep 1
wait_for_text 'Clipboard' 15 || { echo 'FAIL: Clipboard submenu missing' >&2; exit 40; }
read -r x y < <(node_center 'Clipboard'); adb_shell input tap "$x" "$y"
wait_for_text 'Clipboard history timeout' 15 || { echo 'FAIL: clipboard timeout missing from Clipboard submenu' >&2; exit 41; }

echo '[9/13] verify visible current selection summary'
dump_ui
python3 - "$TMP/window.xml" <<'PY'
import re,sys
s=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
if not re.search(r'Current: (?:1 hour|3 hours|6 hours|12 hours|24 hours)',s):
    raise SystemExit('FAIL: current clipboard timeout summary is not visible')
PY

echo '[10/13] verify true dropdown options'
read -r x y < <(node_center 'Clipboard history timeout'); adb_shell input tap "$x" "$y"; sleep 1
dump_ui
for v in '1 hour' '3 hours' '6 hours' '12 hours' '24 hours'; do grep -q "text=\"$v\"" "$TMP/window.xml" || { echo "FAIL: dropdown option missing: $v" >&2; exit 42; }; done
adb_shell input keyevent 4; sleep .5

echo '[11/13] process remains alive after settings/dropdown'
[[ -n "$(adb_shell pidof "$PKG" 2>/dev/null | tr -d '\r')" ]] || { echo 'FAIL: process died during clipboard settings' >&2; exit 43; }

echo '[12/13] final fatal/verifier scan'
"$ADB" logcat -d -v threadtime >"$TMP/logcat-final.txt"
if grep -Ei 'VerifyError|Verifier rejected|FATAL EXCEPTION.*(LatinIME|Meboard)|Process: com\.mekromn\.meboard|am_crash.*com\.mekromn\.meboard' "$TMP/logcat-final.txt" >"$TMP/fatal2.txt"; then cat "$TMP/fatal2.txt" >&2; exit 44; fi

echo '[13/13] PASS: keyboard render + correct submenu + dropdown/current selection + no fatal/verifier crash'
