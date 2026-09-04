#!/system/bin/sh
set -eu

EXPECTED_SOURCE="dd310fe143d095f4065313017df3710780fef2d79d739b9697a950a89d8c127b"
EXPECTED_TARGET="32ae818f8c87bafd3229c16ff5daaec66e3ea638f7c24982dd9f62b0a685d65c"
PKG="com.mekromn.meboard"
WORK="/data/local/tmp/Meboard-stage16-launch-fix-v3.apk"
PART="/data/local/tmp/meboard-v3.patchpart"

SOURCE_PATH=$(pm path "$PKG" | sed -n 's/^package://p' | head -n 1)
[ -n "$SOURCE_PATH" ] || { echo "Meboard is not installed" >&2; exit 20; }
ACTUAL_SOURCE=$(sha256sum "$SOURCE_PATH" | awk '{print $1}')
[ "$ACTUAL_SOURCE" = "$EXPECTED_SOURCE" ] || { echo "Refusing patch: installed base hash $ACTUAL_SOURCE is not expected v2 $EXPECTED_SOURCE" >&2; exit 21; }
cp "$SOURCE_PATH" "$WORK"

# Exact signed-APK byte ranges. They repair only two reused factory
# discriminators plus DEX/APK integrity signatures. No telemetry code returns.
printf '%s' 'hmO8Pw==' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=19611378 conv=notrunc 2>/dev/null
printf '%s' '/OM4HWK5PGQKpqhccoKHaiA/ccNgz76U' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=19611420 conv=notrunc 2>/dev/null
printf '%s' 'DAI=' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=24832187 conv=notrunc 2>/dev/null
printf '%s' 'BhM=' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=24832815 conv=notrunc 2>/dev/null
printf '%s' '9EhgPuWvrlMJFT3/zUzxxqfbRsXORUDmvPUyhA5jyFZHWy/mmTOCkh02nzveYnzjFhVU5KDOLf0VbQO/jvqmcA==' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=109510704 conv=notrunc 2>/dev/null
printf '%s' 'cTznn11IlnwB+K6B2ZgD3xKkAwxy/zrWeCX0Amm5lfaFHmGUcuoRz1LblOygDXjD2aw8Chj9R9aIn5rQglghxtDItLF6SDQ1glHASm8ATZ3WdWIzFx07rjAKw6ZVlXAuoMjsUGMCtpNBvBuOys2XqG8mqwjuL0jwI5RTww4yVMztp8W8Zl6UiNACMi83aDnH5ElpOrAL93CwZMe8JS11lK8r/57u+pwD7WNnGuCu3g2U0Vn8xdp22PDkjg32Bevgb8EzzAHRx0nW21Pupv8U6GxHLx1chDNTK3bRJVyyf9nrGbgNQ881dLgK0CZu9weB0y0RZ4oxBnhByL8afdD9sJ4Xi6gaVUyhsQVju2fTdJMG89R99SmhG5Ae53QlS1317OfjuYH8AHRz+BRe6kY/6J/bx+bGHbWDu7M4lawiYz1BQRezIz1MLrHd99fUBCWCZHsekO18xtQNWOd51GpsmuAamm2q' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=109512252 conv=notrunc 2>/dev/null
printf '%s' 'M7cxQmvQ2oYWBRntKt6Jxl4GlXruYLdB13T08fM4jqHK6pATLLZR/2SvjH0B0AJj3dPY0/UuAm75tFCqmekWevAF9WH4V/cnItYbtcNtcYIa9oM3im45D9x0rRoInZaA9xzY6Ozw6s7dAQvvpXJwHMg1C4MkzJyd2fyRVTy422vqK+mwVSqQCYVIybGvoIEpbv0ruS68X9EylQ==' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=109512610 conv=notrunc 2>/dev/null
printf '%s' 'hmO8Pw==' | base64 -d > "$PART"
dd if="$PART" of="$WORK" bs=1 seek=109514828 conv=notrunc 2>/dev/null

rm -f "$PART"
ACTUAL_TARGET=$(sha256sum "$WORK" | awk '{print $1}')
[ "$ACTUAL_TARGET" = "$EXPECTED_TARGET" ] || { echo "Patched APK hash mismatch: $ACTUAL_TARGET" >&2; rm -f "$WORK"; exit 22; }
pm install -r "$WORK"
INSTALLED_PATH=$(pm path "$PKG" | sed -n 's/^package://p' | head -n 1)
INSTALLED_SHA=$(sha256sum "$INSTALLED_PATH" | awk '{print $1}')
[ "$INSTALLED_SHA" = "$EXPECTED_TARGET" ] || { echo "Installed base hash mismatch: $INSTALLED_SHA" >&2; rm -f "$WORK"; exit 23; }
rm -f "$WORK"
echo "Meboard v3 installed and verified: $INSTALLED_SHA"
