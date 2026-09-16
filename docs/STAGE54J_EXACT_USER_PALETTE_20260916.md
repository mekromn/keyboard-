# Meboard Stage 54j — exact user palette

Stage 54j continues directly from Stage 54i and replaces only the custom Meboard theme colors with the exact palette supplied by the user.

Exact palette:

- `#3A3A3A` dark grey
- `#999999` grey
- `#000000` black
- `#FFFFFF` white
- `#0D0D0D` near-black
- `#5E97F6` cornflower blue
- `#4C4C4C` key grey

Role mapping:

- Keyboard background: `#000000`
- Secondary/dark surface: `#0D0D0D`
- Normal bordered key: `#4C4C4C`
- Pressed/hovered key: `#3A3A3A`
- Dark/special key: `#0D0D0D`
- Dark/special key pressed: `#3A3A3A`
- Primary labels/icons: `#FFFFFF`
- Secondary labels/icons and space indicator: `#999999`
- Accent/action key and all blue states: `#5E97F6`

Regression boundary versus Stage 54i: all four DEX files are byte-identical. Only `AndroidManifest.xml` (version bump), `assets/theme/style_sheet_meboard.binarypb`, and `assets/theme/style_sheet_meboard_border.binarypb` change.

Artifact SHA-256: `4af8488c9a03ec84f8c3c198ad230954b802e2ca8477401923ac6d41740afe32`.
