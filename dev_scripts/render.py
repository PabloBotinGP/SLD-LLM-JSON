#!/usr/bin/env python3
"""
render_pdf.py — Render a PDF to PNG(s).

Usage:
  python render_pdf.py /path/to/file.pdf
  python render_pdf.py /path/to/file.pdf --dpi 450
  python render_pdf.py /path/to/file.pdf --pages 1,4-6 --grayscale

Requires: PyMuPDF (fitz)
  pip install pymupdf
"""

import argparse
import os
import sys
import fitz  # PyMuPDF

def parse_pages(pages_arg, num_pages):
    if not pages_arg:
        return list(range(1, num_pages + 1))
    out = set()
    for part in pages_arg.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a); b = int(b)
            if a < 1 or b < 1 or a > num_pages or b > num_pages or a > b:
                raise ValueError(f"Invalid page range: {part}")
            out.update(range(a, b + 1))
        else:
            p = int(part)
            if p < 1 or p > num_pages:
                raise ValueError(f"Invalid page number: {p}")
            out.add(p)
    return sorted(out)

def render(pdf_path, dpi=300, pages=None, grayscale=False):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    n = doc.page_count
    page_list = parse_pages(pages, n)

    base, _ = os.path.splitext(pdf_path)
    folder_name = base

    # Create a new folder named after the PDF file
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    # Decide naming: single vs multi-page
    single_output = (len(page_list) == 1)

    saved = []
    for page_num in page_list:  # 1-based
        page = doc[page_num - 1]
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if grayscale and pix.n > 1:
            # Convert to grayscale
            pix = fitz.Pixmap(fitz.csGRAY, pix)

        if single_output:
            out_path = os.path.join(folder_name, f"{os.path.basename(base)}.png")
        else:
            out_path = os.path.join(folder_name, f"{os.path.basename(base)}_p{page_num:02d}.png")

        pix.save(out_path)
        saved.append(out_path)

    # Save the original PDF into the folder
    pdf_copy_path = os.path.join(folder_name, f"{os.path.basename(base)}.pdf")
    if not os.path.exists(pdf_copy_path):
        with open(pdf_path, "rb") as original_pdf:
            with open(pdf_copy_path, "wb") as copy_pdf:
                copy_pdf.write(original_pdf.read())

    doc.close()
    return saved

def main():
    ap = argparse.ArgumentParser(description="Render a PDF to PNG(s).")
    ap.add_argument("pdf", help="Path to the PDF file")
    ap.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    ap.add_argument("--pages", type=str, default=None,
                    help="Pages to render, e.g. '1,3-5' (1-based). Default: all pages")
    ap.add_argument("--grayscale", action="store_true",
                    help="Render in grayscale to reduce size")
    args = ap.parse_args()

    try:
        outputs = render(args.pdf, dpi=args.dpi, pages=args.pages, grayscale=args.grayscale)
        if len(outputs) == 1:
            print(f"Saved: {outputs[0]}")
        else:
            print("Saved:")
            for p in outputs:
                print("  ", p)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()