"""Пакує українські картинки карти для патчера: textures/<текстура гри>.rgba.z (RGBA знизу догори, zlib).
Патчеру тоді не потрібні сторонні бібліотеки для читання PNG.
Використання: python make_textures.py ../textures/uk textures
Потрібно: pip install pillow"""
import sys, os, json, zlib
from PIL import Image

# текстура гри (російська) → картинка з textures/uk
MAP = {
    "Map_Front_Full_Russian": "Map_Front_Full_Ukrainian.png",
    "Map_Back_Full_Russian": "Map_Back_Full_Ukrainian.png",
    "Map_Front_Titles_Russian": "Map_Front_Titles_Ukrainian.png",
}

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
manifest = {}
for tex, png in MAP.items():
    im = Image.open(os.path.join(src, png)).convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
    fn = tex + ".rgba.z"
    with open(os.path.join(out, fn), "wb") as f:
        f.write(zlib.compress(im.tobytes(), 9))
    manifest[tex] = {"file": fn, "width": im.width, "height": im.height}
    print(tex, im.size, os.path.getsize(os.path.join(out, fn)) // 1024, "КБ")
with open(os.path.join(out, "textures.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
