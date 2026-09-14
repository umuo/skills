#!/usr/bin/env python3
"""Place ordered page images on A4 without cropping or drawing page content.

Requires Python 3.10+, Pillow and reportlab. Manifest: {"pages": ["page.png"]}.
Paths are relative to the manifest; explicit --images retain argument order.
"""

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def page_image(path):
    with Image.open(path) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError(f"Multi-frame image is not a single page: {path}")
        oriented = ImageOps.exif_transpose(source)
        rgba = oriented.convert("RGBA")
        white = Image.new("RGBA", rgba.size, "white")
        white.alpha_composite(rgba)
        return white.convert("RGB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--manifest", type=Path)
    inputs.add_argument("--images", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--margin-mm", type=float, default=0)
    parser.add_argument("--force", action="store_true", help="Replace existing PDF")
    args = parser.parse_args()
    if not math.isfinite(args.margin_mm) or not 0 <= args.margin_mm < 105:
        parser.error("--margin-mm must be finite and between 0 (inclusive) and 105")

    temporary = None
    try:
        if args.manifest:
            data = json.loads(args.manifest.read_text(encoding="utf-8"))
            pages = data.get("pages") if isinstance(data, dict) else None
            if not isinstance(pages, list) or not pages or not all(
                isinstance(item, str) and item.strip() for item in pages
            ):
                raise ValueError('Manifest requires a non-empty "pages" array of paths')
            paths = [(args.manifest.resolve().parent / item).resolve() for item in pages]
        else:
            paths = [path.resolve() for path in args.images]
        if len(set(paths)) != len(paths):
            raise ValueError("Duplicate image paths: check page order")
        output = args.output.resolve()
        if output.suffix.lower() != ".pdf":
            raise ValueError("Output must have a .pdf extension")
        if output in paths or (args.manifest and output == args.manifest.resolve()):
            raise ValueError("Output cannot overwrite an input")
        if output.exists() and not args.force:
            raise ValueError(f"Output exists; use another name or --force: {output}")
        # Validate all pages before creating an output file.
        for path in paths:
            with page_image(path) as checked:
                checked.load()
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".a4-pages-", suffix=".pdf", dir=output.parent)
        os.close(fd)
        pdf = canvas.Canvas(temporary, pagesize=A4, pageCompression=1)
        pdf.setTitle(output.stem)
        width, height = A4
        margin = args.margin_mm * 72 / 25.4
        reports = []
        for index, path in enumerate(paths, 1):
            with page_image(path) as picture:
                scale = min((width - 2 * margin) / picture.width,
                            (height - 2 * margin) / picture.height)
                draw_w, draw_h = picture.width * scale, picture.height * scale
                dpi = 72 / scale
                pdf.drawImage(ImageReader(picture), (width - draw_w) / 2,
                              (height - draw_h) / 2, width=draw_w, height=draw_h)
                pdf.showPage()
                reports.append(f"Page {index}: {path.name}, {picture.width}x{picture.height}, "
                               f"effective DPI {dpi:.1f}" +
                               (" — LOW RESOLUTION: inspect print legibility" if dpi < 200 else ""))
        pdf.save()
        if args.force:
            os.replace(temporary, output)
        else:
            # Atomic publish without clobbering a concurrently created destination.
            os.link(temporary, output)
            os.unlink(temporary)
        temporary = None
        print("\n".join(reports))
        print(f"Saved {len(paths)} A4 pages (210 x 297 mm): {output}")
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
