# __init__ module

def normalize_image_to_jpeg(src_path: str) -> str:
    """Convert various input formats to a JPEG with corrected orientation.

    Uses Pillow if available; otherwise returns the original path.
    """
    try:
        from PIL import Image, ImageOps
        import os
        # Load and correct orientation via EXIF
        with Image.open(src_path) as im:
            im = ImageOps.exif_transpose(im)
            # Convert to RGB
            if im.mode in ("RGBA", "P"):  # remove alpha
                background = Image.new("RGB", im.size, (255, 255, 255))
                background.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
                im = background
            else:
                im = im.convert("RGB")
            # Save as JPEG next to original
            base = os.path.splitext(os.path.basename(src_path))[0]
            dst_dir = os.path.dirname(src_path)
            dst_path = os.path.join(dst_dir, f"{base}.jpg")
            im.save(dst_path, format="JPEG", quality=92)
            return dst_path
    except Exception:
        pass
    return src_path