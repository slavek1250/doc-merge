from pathlib import Path
from DocMerger.doc_merger import DocMerger

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, required=True, help="Input directory to glob pdf, docx files in")
    parser.add_argument("--output_pdf", type=Path, required=True, help="Output pdf file path")
    parser.add_argument("--align", type=int, default=2, help="Before merging, align the number of pages of each document to be a multiple of the align value")
    args = parser.parse_args()

    DocMerger(args.input_dir, args.output_pdf, args.align).execute()

if __name__ == "__main__":
    main()
