"""Cut the Gemini pet sheets into transparent PNG sprite sheets.

Run: python3 tools/make-pet-sprites.py SRC_DIR [OUT_DIR]  (needs Pillow)
SRC_DIR holds baby/brawler/climber/stomper.jpg and *-walk.jpg. OUT_DIR defaults to pet/.
"""
import sys
from collections import deque
from pathlib import Path
from PIL import Image

BG = (10, 10, 10)    # sheet background, #0a0a0a
TOL = 30             # RGB distance counted as background
SPECKLE = 24         # luminance under which a pixel touching transparency is JPG noise
OUT_CELL = 128
FORMS = ["baby", "brawler", "climber", "stomper"]


def near_bg(px):
    return sum((a - b) ** 2 for a, b in zip(px[:3], BG)) <= TOL * TOL


def key_cell(cell):
    """Make background transparent by flood-filling in from the border, so interior outlines survive."""
    img = cell.convert("RGBA")
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.extend([(x, 0), (x, h - 1)])
    for y in range(h):
        q.extend([(0, y), (w - 1, y)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]:
            continue
        seen[y * w + x] = 1
        if not near_bg(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    # Dark speckle left against the cleared area.
    dead = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0 or (r * 299 + g * 587 + b * 114) / 1000 >= SPECKLE:
                continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] == 0
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dead.append((x, y))
    for x, y in dead:
        px[x, y] = (0, 0, 0, 0)
    return img


def small(cell):
    return cell.resize((OUT_CELL, OUT_CELL), Image.LANCZOS)


def mood_sheet(src):
    sheet = Image.open(src)
    cs = sheet.width // 4
    out = Image.new("RGBA", (OUT_CELL * 4, OUT_CELL * 4), (0, 0, 0, 0))
    for r in range(4):
        for c in range(4):
            cell = sheet.crop((c * cs, r * cs, (c + 1) * cs, (r + 1) * cs))
            out.paste(small(key_cell(cell)), (c * OUT_CELL, r * OUT_CELL))
    return out


def walk_strip(src):
    sheet = Image.open(src)
    cw, ch = sheet.width // 4, sheet.height
    pad = (cw - ch) // 2
    out = Image.new("RGBA", (OUT_CELL * 4, OUT_CELL), (0, 0, 0, 0))
    for c in range(4):
        cell = sheet.crop((c * cw + pad, 0, c * cw + pad + ch, ch))
        out.paste(small(key_cell(cell)), (c * OUT_CELL, 0))
    return out


def save(img, path):
    """256-colour PNG keeps each sheet small. Pixel art loses nothing visible."""
    img.quantize(colors=256, method=Image.FASTOCTREE, dither=Image.NONE).save(path, optimize=True)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "pet"
    out.mkdir(parents=True, exist_ok=True)
    for f in FORMS:
        save(mood_sheet(src / f"{f}.jpg"), out / f"{f}.png")
        save(walk_strip(src / f"{f}-walk.jpg"), out / f"{f}-walk.png")
        print("wrote", f)


if __name__ == "__main__":
    main()
