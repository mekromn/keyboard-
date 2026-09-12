#!/system/bin/sh
# One-shot, local-only Meboard diagnostic capture. Run in LADB/ADB shell.
# No app data is cleared, no permissions/settings are changed, no microphone
# recording is started, and nothing is uploaded. Logs CAN contain dictated text.
# The Android log output is restricted to this installed Meboard app's UID.
set -u
PKG=com.mekromn.meboard
OUTDIR=${1:-/sdcard/Download}
fail() { echo "Meboard capture: $*" >&2; exit 1; }
case "$(id -u)" in
  0|2000) ;;
  *) fail 'Run this in LADB or an authorized ADB shell, not ordinary Termux.' ;;
esac
USER_ID=$(am get-current-user 2>/dev/null) || fail 'Cannot identify the active Android user.'
case "$USER_ID" in ''|*[!0-9]*) fail 'Invalid Android user ID.';; esac
PACKAGES=$(cmd package list packages -U --user "$USER_ID" "$PKG" 2>/dev/null) || fail 'Cannot query the installed package.'
APP_UID=$(printf '%s\n' "$PACKAGES" | sed -n 's/^package:com\.mekromn\.meboard uid:\([0-9][0-9]*\).*$/\1/p')
case "$APP_UID" in ''|*[!0-9]*) fail 'Could not resolve exactly one Meboard UID; refusing an unfiltered capture.';; esac
HELP=$(logcat --help 2>&1) || fail 'logcat is unavailable.'
printf '%s\n' "$HELP" | grep -q -- '--uid' || fail 'This logcat does not support UID filtering; refusing an unfiltered capture.'
mkdir -p "$OUTDIR" || fail 'Cannot create the output directory.'
STAMP=$(date '+%Y%m%d-%H%M%S')
REPORT="$OUTDIR/Meboard-voice-$STAMP-$$.txt"
(umask 077; : > "$REPORT") || fail 'Cannot create the report.'
{
  echo 'MEBOARD VOICE DIAGNOSTIC — EXISTING APP LOGS ONLY'
  echo 'Review before sharing: existing logs may contain recognized text or other app data.'
  echo 'No audio recording, upload, setting change, app-data clearing, or log clearing was performed.'
  echo "Capture time: $(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "Package: $PKG"
  echo "Active Android user: $USER_ID"
  echo "App UID filter: $APP_UID"
  echo "Android release: $(getprop ro.build.version.release)"
  echo "Android SDK: $(getprop ro.build.version.sdk)"
  APK_PATH=$(pm path --user "$USER_ID" "$PKG" 2>/dev/null | sed -n 's/^package://p' | grep '/base\.apk$' | head -n 1)
  if [ -n "$APK_PATH" ] && [ -r "$APK_PATH" ]; then
    HASH=$(sha256sum "$APK_PATH" 2>/dev/null)
    echo "Installed base APK SHA-256: ${HASH%% *}"
  else
    echo 'Installed base APK SHA-256: unavailable (no fallback assumption made)'
  fi
  echo
  echo '--- Existing main/system/crash log messages from Meboard UID ---'
} >> "$REPORT"
if logcat -d -t 6000 -b main -b system -b crash -v threadtime --uid="$APP_UID" '*:V' >> "$REPORT" 2>&1; then
  echo
  echo "Saved: $REPORT"
  echo 'This captures only available existing logs; no lines does not mean no bug.'
  echo 'Review the text before sharing it. External speech-service logs are not included.'
else
  echo "logcat failed. Diagnostic output is in: $REPORT" >&2
  exit 2
fi
