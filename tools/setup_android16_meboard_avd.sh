#!/usr/bin/env bash
set -euo pipefail
SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}"
export ANDROID_SDK_ROOT="$SDK_ROOT"
SDKMANAGER="$SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$SDK_ROOT/cmdline-tools/latest/bin/avdmanager"
EMULATOR="$SDK_ROOT/emulator/emulator"
IMAGE="${MEBOARD_SYSTEM_IMAGE:-system-images;android-36;google_apis;x86_64}"
AVD="${MEBOARD_AVD_NAME:-meboard_android16}"
DEVICE="${MEBOARD_AVD_DEVICE:-pixel_9_pro_xl}"
[[ -x "$SDKMANAGER" ]] || { echo "sdkmanager not found at $SDKMANAGER" >&2; exit 2; }
yes | "$SDKMANAGER" --licenses >/dev/null
"$SDKMANAGER" "platform-tools" "emulator" "$IMAGE"
if ! "$AVDMANAGER" list device | grep -q "id:.*$DEVICE"; then DEVICE="pixel_8_pro"; fi
echo no | "$AVDMANAGER" create avd --force --name "$AVD" --package "$IMAGE" --device "$DEVICE"
cat >> "$HOME/.android/avd/$AVD.avd/config.ini" <<EOF
hw.keyboard=yes
hw.gpu.mode=auto
showDeviceFrame=no
EOF
echo "Created $AVD"
echo "Start: $EMULATOR -avd $AVD -no-snapshot -no-boot-anim"
