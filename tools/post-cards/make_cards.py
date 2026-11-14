"""Branded Xonomy post cards (1200x1200) in the style of the website's og image.
Usage: python3 -I make_cards.py cards.json OUTDIR
"""
import json, sys, os
from PIL import Image, ImageDraw, ImageFont, features

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
W = H = 1200
BG = (14, 21, 20)
GRID = (22, 34, 31)
ACCENT = (61, 220, 174)
INK = (230, 239, 236)
MUTED = (166, 184, 179)
FRAME = (32, 64, 56)


def font(name, size, wght=None):
    f = ImageFont.truetype(os.path.join(FD, name), size,
                           layout_engine=ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


MICH = lambda s: font("michroma-latin-400.ttf", s)
MONO = lambda s: font("jetbrains-mono-variable-latin.ttf", s, 400)
AR = lambda s, w=600: font(f"ibm-plex-sans-arabic-{w}.ttf", s)


def tracked(d, xy, text, f, fill, track=0, anchor_right=False):
    x, y = xy
    widths = [d.textlength(c, font=f) + track for c in text]
    total = sum(widths) - track if text else 0
    if anchor_right:
        x -= total
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill)
        x += w
    return total


def tracked_width(d, text, f, track):
    return sum(d.textlength(c, font=f) + track for c in text) - (track if text else 0)


def wrap(d, text, f, maxw, track=0):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tracked_width(d, t, f, track) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def cubic(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        pts.append((mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
                    mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]))
    return pts


def logo(d, x, y, size):
    s = size / 200.0
    P = lambda px, py: (x + px * s, y + py * s)
    d.rectangle([P(10, 10), P(190, 190)], outline=FRAME, width=2)
    for v in (70, 130):
        d.line([P(10, v), P(190, v)], fill=GRID, width=1)
        d.line([P(v, 10), P(v, 190)], fill=GRID, width=1)
    leaf = cubic((50, 150), (50, 100), (80, 60), (150, 50)) + cubic((150, 50), (150, 120), (110, 150), (50, 150))
    d.line([P(*p) for p in leaf], fill=ACCENT, width=max(3, int(6 * s)), joint="curve")
    d.line([P(50, 150), P(110, 90)], fill=ACCENT, width=max(3, int(6 * s)))


def card(spec, out):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for v in range(0, W, 60):
        d.line([(v, 0), (v, H)], fill=GRID, width=1)
        d.line([(0, v), (W, v)], fill=GRID, width=1)
    m = 48
    d.rectangle([m, m, W - m, H - m], outline=FRAME, width=1)
    L = 30
    for cx, cy, sx, sy in ((m, m, 1, 1), (W - m, H - m, -1, -1)):
        d.line([(cx, cy), (cx + sx * L, cy)], fill=ACCENT, width=4)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=ACCENT, width=4)

    rtl = spec.get("rtl", False)
    left, right = 110, W - 110
    # logo + wordmark (always LTR, top-left)
    logo(d, left, 110, 76)
    tracked(d, (left + 100, 112), "XONOMY", MICH(38), INK, track=8)
    tracked(d, (left + 102, 166), "POWERED BY OPEN2X", MONO(18), MUTED, track=4)

    y = 330
    if rtl:
        f = AR(30, 600)
        d.text((right, y), spec["label"], font=f, fill=ACCENT, anchor="ra", direction="rtl")
        y += 80
        hf = AR(78, 700)
        lines = wrap(d, spec["headline"], hf, right - left)
        for ln in lines:
            d.text((right, y), ln, font=hf, fill=INK, anchor="ra", direction="rtl")
            y += 118
        if spec.get("sub"):
            y += 20
            sf = AR(36, 500)
            for ln in wrap(d, spec["sub"], sf, right - left):
                d.text((right, y), ln, font=sf, fill=MUTED, anchor="ra", direction="rtl")
                y += 58
    else:
        tracked(d, (left, y), spec["label"].upper(), MONO(24), ACCENT, track=5)
        y += 70
        size = spec.get("size", 66)
        hf = MICH(size)
        for ln in wrap(d, spec["headline"].upper(), hf, right - left, track=2):
            tracked(d, (left, y), ln, hf, INK, track=2)
            y += int(size * 1.32)
        if spec.get("sub"):
            y += 24
            sf = font("manrope-variable-latin.ttf", 36, 500)
            for ln in wrap(d, spec["sub"], sf, right - left):
                d.text((left, y), ln, font=sf, fill=MUTED)
                y += 52

    if spec.get("facts"):
        fy = H - 330
        x = left
        for n, l in (("9", "sectors"), ("51", "activities"), ("445", "criteria checked"), ("AR·EN", "fully bilingual")):
            nw = tracked(d, (x, fy), n, MICH(46), ACCENT, track=2)
            lw = tracked(d, (x, fy + 70), l, MONO(20), MUTED, track=1)
            x += max(nw, lw) + 64

    foot = spec.get("foot", "xonomy.open2x.io  ·  Request a demo")
    if rtl:
        # Arabic call to action on the right, the web address (Latin) on the left
        d.text((right, H - 166), spec.get("cta", ""), font=AR(30, 500), fill=MUTED, anchor="ra", direction="rtl")
        tracked(d, (left, H - 160), foot, MONO(24), MUTED, track=2)
    else:
        tracked(d, (left, H - 160), foot, MONO(24), MUTED, track=2)
    im.save(out, "JPEG", quality=92, optimize=True, progressive=True)


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(sys.argv[2], exist_ok=True)
    for s in specs:
        p = os.path.join(sys.argv[2], s["id"] + ".jpg")
        card(s, p)
        print("wrote", p)
