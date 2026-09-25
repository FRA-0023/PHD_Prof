"""
slice_pdf.py
------------
Utility to slice specific page ranges or sections from large academic manuals and books.
Zero external bloat: uses PyMuPDF (fitz) for fast, vector-perfect extraction.
"""

import sys
import argparse
import pathlib
import fitz
from typing import List, Tuple

def parse_page_range(range_str: str, max_pages: int) -> List[int]:
    """
    Parses a string of 1-based page ranges (e.g. '30-31, 37-43, 46, 60-61')
    into a sorted list of unique 1-based page integers.
    """
    pages = set()
    parts = [p.strip() for p in range_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            sub = part.split("-")
            start = int(sub[0].strip())
            end = int(sub[1].strip())
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                if 1 <= p <= max_pages:
                    pages.add(p)
        else:
            p = int(part.strip())
            if 1 <= p <= max_pages:
                pages.add(p)
    return sorted(list(pages))

def extract_pdf_pages(
    input_path: pathlib.Path,
    pages: List[int],
    output_path: pathlib.Path,
) -> None:
    """
    Extracts specified 1-based pages from input_path and saves them into output_path.
    """
    doc = fitz.open(str(input_path))
    new_doc = fitz.open()
    for p in pages:
        # fitz uses 0-based page indexes
        new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    new_doc.save(str(output_path))
    new_doc.close()
    doc.close()
    print(f"  [OK] Creato '{output_path.name}' ({len(pages)} pagine).")

def main():
    parser = argparse.ArgumentParser(description="Slice specific pages or chapters from large PDFs.")
    parser.add_argument("-i", "--input", help="Path to input PDF")
    parser.add_argument("-p", "--pages", help="Page range (e.g. '30-31,37-43,46,60-61')")
    parser.add_argument("-o", "--output", help="Path to output PDF")
    args = parser.parse_args()

    input_path_str = args.input
    if not input_path_str:
        input_path_str = input("Percorso PDF sorgente: ").strip()
    
    input_path = pathlib.Path(input_path_str).expanduser().resolve()
    if not input_path.is_file() or input_path.suffix.lower() != ".pdf":
        print(f"[!] File non trovato o non valido: {input_path}")
        sys.exit(1)

    doc = fitz.open(str(input_path))
    total_pages = len(doc)
    doc.close()
    print(f"File aperto: '{input_path.name}' ({total_pages} pagine totali).")

    pages_str = args.pages
    if not pages_str:
        print("\nInserisci le pagine da estrarre (1-based, es: '30-31, 37-43, 46, 60-61'):")
        pages_str = input("Pagine: ").strip()

    pages = parse_page_range(pages_str, total_pages)
    if not pages:
        print("[!] Nessuna pagina valida specificata.")
        sys.exit(1)

    output_path_str = args.output
    if not output_path_str:
        default_out = input_path.parent / f"{input_path.stem}_excerpt.pdf"
        out_prompt = input(f"Percorso output [default: {default_out.name}]: ").strip()
        output_path = pathlib.Path(out_prompt).expanduser().resolve() if out_prompt else default_out
    else:
        output_path = pathlib.Path(output_path_str).expanduser().resolve()

    extract_pdf_pages(input_path, pages, output_path)

if __name__ == "__main__":
    main()
