# Branded post cards

Generates 1200x1200 Xonomy post images in the style of the website's social image, so posts can
advertise outcomes without showing product screens.

1. Convert the website fonts to TTF into `tools/post-cards/fonts/` (not committed):
   `pip install fonttools brotli` then convert `xonomy-website/src/assets/fonts/*.woff2` with fontTools
   (`TTFont(path); t.flavor=None; t.save(name.ttf)`).
2. Edit `cards.json` (`label`, `headline`, optional `sub`, `facts`, `size`; Arabic cards use `rtl`, `cta`).
3. `python3 make_cards.py cards.json out/`
