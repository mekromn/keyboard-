# Stage 54g replay notes

Base branch: `meboard/stage54f-stock-softkey-icon-resolver-20260915`.

Text/code edits:
1. `smali/qyk.smali`
   - Keep the existing `H(context)` / `G(context)` resolution first.
   - If it returns a theme, return it unchanged.
   - Otherwise instantiate `qyk("assets:theme_package_metadata_meboard.binarypb", false)` from `A(context)` and `qyk("assets:theme_package_metadata_meboard.binarypb", true)` from `z(context)`.
2. `MeboardTestPreference.smali`
   - title `Keyboard test`
   - keep subtitle `Open a text field to test typing and voice input`
   - resolve/apply drawable `meboard_ic_keyboard_test`
3. `MeboardTestPreference$ClickListener.smali`
   - dialog title `Keyboard test`
4. `res/xml/settings.xml`
   - remove `RateUsPreference`
   - remove the `Help & feedback` header
5. `res/xml/setting_about.xml`
   - replace inherited links with Meboard app icon/name, version/build, privacy-model summary, and open-source licenses.
6. Register `assets:theme_package_metadata_meboard.binarypb` in both normal theme package arrays.
7. Replace adaptive launcher foreground/background assets at all density buckets and set the adaptive monochrome layer to `@drawable/meboard_ic_keyboard_test`.

Theme palette is fixed in `style_sheet_meboard.binarypb`:
`#000000 #353A42 #4B4C4F #626366 #404245 #FFFFFF #B7B9C0 #147BF6 #3199FE #075EEA`.

Reference payload SHA-256 values:
- `style_sheet_meboard.binarypb`: `91520888959c4725c97a83d2e0217ef21f13e7747e3e65420ad40898972431d5`
- empty `style_sheet_meboard_border.binarypb`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `theme_package_metadata_meboard.binarypb`: `0ca987686223907ebd19f7b2821fd38cdbc64e3b450023fdd8dcef21b7a2d2e2`
- `meboard_ic_keyboard_test.xml`: `a4ce722196d1f623b9da3431b42a62d3aab84d2510309af2bc1604467d36c307`
- xxxhdpi launcher foreground: `f3ef09a5bdec113758ba3cb5e3f2470e93ecfc75de457d7ca9bcce794fb9993b`
- xxxhdpi launcher background: `00fae582e2fbfd2a57521d11df2319573e83a64645f3f02fd8d0493953406fd8`

Do not commit signing material. Sign with the existing stable Meboard key only after fresh decode/build gates pass.