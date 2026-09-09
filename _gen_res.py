# -*- coding: utf-8 -*-
"""把 icon512.png 转成 Android 各密度图标资源"""
import os
from PIL import Image

SRC = r"C:\Users\Lenovo\Desktop\课文音频\..\..\Documents\Default Project\listen\_icon\icon512.png"
SRC = os.path.normpath(SRC)
RES = r"C:\Users\Lenovo\.workbuddy\projects\listen-apk\app\src\main\res"

big = Image.open(SRC).convert("RGBA")

# 1) 传统方形图标（Android 7 及以下）
for folder, size in [("mipmap-mdpi", 48), ("mipmap-hdpi", 72),
                     ("mipmap-xhdpi", 96), ("mipmap-xxhdpi", 144),
                     ("mipmap-xxxhdpi", 192)]:
    d = os.path.join(RES, folder)
    os.makedirs(d, exist_ok=True)
    im = big.resize((size, size), Image.LANCZOS)
    im.save(os.path.join(d, "ic_launcher.png"), optimize=True)
    im.save(os.path.join(d, "ic_launcher_round.png"), optimize=True)
    print(folder, size)

# 2) 自适应图标前景：抠出白色图形，缩到中心 61% 安全区
w, h = big.size
px = big.load()
fg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
fp = fg.load()
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        m = min(r, g, b)
        na = int(max(0, min(255, (m - 150) * 255 / 105)))
        if na > 0:
            fp[x, y] = (255, 255, 255, na)

bbox = fg.getbbox()
fg = fg.crop(bbox)
cw, ch = fg.size
target = int(432 * 0.66)
scale = target / max(cw, ch)
fg = fg.resize((max(1, int(cw * scale)), max(1, int(ch * scale))), Image.LANCZOS)

canvas = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
canvas.paste(fg, ((432 - fg.width) // 2, (432 - fg.height) // 2), fg)
dn = os.path.join(RES, "drawable-nodpi")
os.makedirs(dn, exist_ok=True)
canvas.save(os.path.join(dn, "ic_foreground.png"), optimize=True)
print("foreground", canvas.size, "content", fg.size)

# 3) Play 商店用的 512 图标
os.makedirs(os.path.join(RES, "drawable-nodpi"), exist_ok=True)
big.save(os.path.join(dn, "ic_store.png"), optimize=True)
print("done")
