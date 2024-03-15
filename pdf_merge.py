from pypdf import PdfWriter
from pdfreader import PDFDocument
from pathlib import Path
from reportlab.pdfgen import canvas
from time import sleep
import docx2pdf
import tempfile
import argparse


def get_number_of_pages_in_pdf(pdf_file_path):
    with open(pdf_file_path, 'rb') as pdf:
        pdf_doc = PDFDocument(pdf)
        number_of_pages = len(list(pdf_doc.pages()))
        return number_of_pages

def create_empty_page(empty_page_tmp_dir, src_pdf_file_path):
    with open(src_pdf_file_path, 'rb') as pdf:
        pdf_doc = PDFDocument(pdf)
        pdf_pages_list = list(pdf_doc.pages())
        pdf_mediabox = pdf_pages_list[0].MediaBox
        pdf_pagesize = (pdf_mediabox[2], pdf_mediabox[3])
        empty_page_file_path = f"{empty_page_tmp_dir}/empty.pdf"
        empty_page_canvas = canvas.Canvas(empty_page_file_path, pagesize=pdf_pagesize)
        empty_page_canvas.showPage()
        empty_page_canvas.save()
        return empty_page_file_path

def align_number_of_pages_in_pdf_file_to_multiplier(pdf_file_path, dst_dir_path, empty_page_pdf_file_path, number_of_pages_multiplier):
    pdf_file_name = Path(pdf_file_path).name
    number_of_pages = get_number_of_pages_in_pdf(pdf_file_path)
    remaining_pages = number_of_pages % number_of_pages_multiplier
    number_of_empty_pages_to_add = (number_of_pages_multiplier - remaining_pages) % number_of_pages_multiplier
    with PdfWriter() as writer:
        writer.append(pdf_file_path)
        print(f"{pdf_file_name}: has {number_of_pages} pages, adding {number_of_empty_pages_to_add} empty pages")
        for _ in range(number_of_empty_pages_to_add):
            writer.append(empty_page_pdf_file_path)
        writer.write(f"{dst_dir_path}/{pdf_file_name}")

def convert_doc_to_pdf(doc_file_path, dst_pdf_file_path):
    extension = Path(doc_file_path).suffix
    if extension == ".docx":
        docx2pdf.convert(doc_file_path, dst_pdf_file_path)
    else:
        raise RuntimeError(f"Invalid extension {extension}")

def align_number_of_pages_of_all_pdfs_in_dir_to_multiplier(src_dir_path, dst_dir_path, empty_page_tmp_dir, number_of_pages_multiplier):
    pdfs_in_src_dir = list(Path(src_dir_path).glob('*.pdf'))
    is_first_file = True
    for pdf_file in pdfs_in_src_dir:
        if is_first_file:
            empty_page_pdf_file_path = create_empty_page(empty_page_tmp_dir, pdf_file)
        is_first_file = False
        align_number_of_pages_in_pdf_file_to_multiplier(pdf_file, dst_dir_path, empty_page_pdf_file_path, number_of_pages_multiplier)

def align_number_of_pages_of_all_documents_in_dir_to_multiplier(src_dir_path, dst_dir_path, empty_page_tmp_dir, number_of_pages_multiplier):
    docx_files = list(Path(src_dir_path).glob("*.doc*"))
    if len(docx_files) > 0:
        with tempfile.TemporaryDirectory() as docx_to_pdfs_dir:
            for docx_file in docx_files:
                docx_file_stem = Path(docx_file).stem
                docx_file_name = Path(docx_file).name
                dst_pdf_file_path = f"{docx_to_pdfs_dir}/{docx_file_stem}.pdf"
                print(f"Converting to pdf: {docx_file_name}")
                convert_doc_to_pdf(docx_file, dst_pdf_file_path)
            align_number_of_pages_of_all_pdfs_in_dir_to_multiplier(docx_to_pdfs_dir, dst_dir_path, empty_page_tmp_dir, number_of_pages_multiplier)
    align_number_of_pages_of_all_pdfs_in_dir_to_multiplier(src_dir_path, dst_dir_path, empty_page_tmp_dir, number_of_pages_multiplier)

def merge_all_pdfs(src_dir_path, dst_pdf_file_path):
    pdfs_in_src_dir = list(Path(src_dir_path).glob('*.pdf'))
    print(f"Creating output PDF file: {dst_pdf_file_path}")
    with PdfWriter() as writer:
        for pdf_file in pdfs_in_src_dir:
            writer.append(pdf_file)
        writer.write(dst_pdf_file_path)
        print(f"Number of files merged: {len(pdfs_in_src_dir)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, required=True, help="Input directory to glob pdfs in")
    parser.add_argument("--output_pdf", type=Path, required=True, help="Output pdf file path")
    parser.add_argument("--multiplier", type=int, default=2, help="Multiplier of number of pages for each document before merging")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as empty_page_tmp_dir:
        with tempfile.TemporaryDirectory() as pdfs_tmp_dir:
            align_number_of_pages_of_all_documents_in_dir_to_multiplier(args.input_dir, pdfs_tmp_dir, empty_page_tmp_dir, args.multiplier)
            merge_all_pdfs(pdfs_tmp_dir, args.output_pdf)
            print("Done! Thank you :)")


if __name__ == "__main__":
    main()
