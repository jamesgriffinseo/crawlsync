#!/usr/bin/env python3
"""
Generate CrawlSync app icons.
  macOS  → CrawlSync.icns  (requires iconutil, bundled with Xcode CLI tools)
  Windows → CrawlSync.ico   (pure Pillow, no extra tools needed)

Run automatically by build_app.sh / build_app.bat.
"""

import os
import platform
import shutil
import subprocess
from PIL import Image, ImageDraw

# macOS iconset sizes
ICNS_SIZES = {
    16:   ["icon_16x16.png"],
    32:   ["icon_16x16@2x.png", "icon_32x32.png"],
    64:   ["icon_32x32@2x.png"],
    128:  ["icon_128x128.png"],
    256:  ["icon_128x128@2x.png", "icon_256x256.png"],
    512:  ["icon_256x256@2x.png", "icon_512x512.png"],
    1024: ["icon_512x512@2x.png"],
}

# Windows ICO embedded sizes (largest first so Pillow picks the best default)
ICO_SIZES = [256, 128, 64, 48, 32, 16]


def gradient_bg(size):
    img = Image.new("RGBA", (size, size))
    c1 = (29, 18, 82)    # deep indigo
    c2 = (94, 36, 160)   # vivid purple
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        img.paste((r, g, b, 255), (0, y, size, y + 1))
    return img


def squircle_mask(size):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.225), fill=255)
    return mask


def draw_symbol(draw, size):
    s = size / 1024
    white = (255, 255, 255, 215)
    lw = max(1, int(30 * s))

    root = (int(512 * s), int(285 * s))
    children = [(int(256 * s), int(720 * s)), (int(512 * s), int(720 * s)), (int(768 * s), int(720 * s))]

    for child in children:
        draw.line([root, child], fill=white, width=lw)

    for i, (x, y) in enumerate([root] + children):
        r = int((56 if i == 0 else 46) * s)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=white)


def make_icon(size):
    bg = gradient_bg(size)
    bg.putalpha(squircle_mask(size))
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_symbol(ImageDraw.Draw(overlay), size)
    return Image.alpha_composite(bg, overlay)


def build_icns():
    """macOS: build CrawlSync.icns via iconutil."""
    iconset = "CrawlSync.iconset"
    os.makedirs(iconset, exist_ok=True)

    for size, names in ICNS_SIZES.items():
        img = make_icon(size)
        for name in names:
            img.save(os.path.join(iconset, name))
        print(f"  {size}x{size}")

    r = subprocess.run(
        ["iconutil", "-c", "icns", iconset, "-o", "CrawlSync.icns"],
        capture_output=True, text=True,
    )
    shutil.rmtree(iconset)

    if r.returncode != 0:
        print(f"iconutil error: {r.stderr}")
        return False

    print("  CrawlSync.icns ✓")
    return True


def build_ico():
    """All platforms: build CrawlSync.ico using Pillow (no extra tools needed)."""
    images = [make_icon(s).convert("RGBA") for s in ICO_SIZES]
    # Pillow ICO: save largest image, embed all sizes
    images[0].save(
        "CrawlSync.ico",
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=images[1:],
    )
    print("  CrawlSync.ico ✓")
    return True


def main():
    sys_platform = platform.system()
    print(f"Generating icons for {sys_platform}...")

    if sys_platform == "Darwin":
        build_icns()
        build_ico()   # also generate .ico so cross-compiling is possible
    elif sys_platform == "Windows":
        build_ico()
    else:
        # Linux / CI — generate both where possible
        build_ico()
        print("  (Skipping .icns — iconutil is macOS only)")


if __name__ == "__main__":
    main()
