"""
shrink oversized photos so uploads from Pages CMS don't bloat the site.

usage: python _scripts/shrink_images.py [file ...]
with no files, checks everything in images/.
"""

import sys
from pathlib import Path
from PIL import Image, ImageOps

# longest side, in pixels, that a photo is allowed to have
MAX_SIDE = 2400

# jpgs bigger than this get recompressed even if not too wide
MAX_JPG_BYTES = 1024 * 1024

# jpg quality to save at (good enough for the web, much smaller than phone photos)
QUALITY = 82

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def shrink(path):
    """resize/recompress one image in place. return true if it changed."""
    is_jpg = path.suffix.lower() in {".jpg", ".jpeg"}
    size_before = path.stat().st_size

    with Image.open(path) as image:
        too_big = max(image.size) > MAX_SIDE
        too_heavy = is_jpg and size_before > MAX_JPG_BYTES
        if not too_big and not too_heavy:
            return False

        # rotate phone photos upright before metadata is dropped
        image = ImageOps.exif_transpose(image)
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)

        # keep color profile, drop the rest (camera details, gps location)
        options = {"icc_profile": image.info.get("icc_profile")}
        if is_jpg:
            image = image.convert("RGB")
            options.update(quality=QUALITY, optimize=True, progressive=True)
        else:
            options.update(optimize=True)

        temp = path.with_name(path.name + ".tmp")
        image.save(temp, format=Image.registered_extensions()[path.suffix.lower()], **options)

    # keep the original if recompressing didn't clearly help (also stops a photo
    # that's already been recompressed from being recompressed again on every run)
    if temp.stat().st_size > size_before * 0.9 and not too_big:
        temp.unlink()
        return False

    temp.replace(path)
    print(f"{path}: {size_before / 1e6:.1f} MB -> {path.stat().st_size / 1e6:.1f} MB")
    return True


files = [Path(arg) for arg in sys.argv[1:]] or list(Path("images").rglob("*"))
files = [file for file in files if file.is_file() and file.suffix.lower() in EXTENSIONS]

changed = 0
for file in files:
    try:
        changed += shrink(file)
    except Exception as error:
        print(f"{file}: skipped ({error})")

print(f"Shrank {changed} of {len(files)} image(s)")
