from pypdf import PdfWriter
from pdfreader import PDFDocument
from pathlib import Path
from reportlab.pdfgen import canvas
from time import sleep
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

def make_even_pages_in_pdf_file(pdf_file_path, dst_dir_path, empty_page_pdf_file_path):
    pdf_file_name = Path(pdf_file_path).name
    number_of_pages = get_number_of_pages_in_pdf(pdf_file_path)
    is_even = (number_of_pages % 2) == 0
    with PdfWriter() as writer:
        writer.append(pdf_file_path)
        if is_even:
            print(f"{pdf_file_name}: has even number of pages ({number_of_pages})")
        else:
            writer.append(empty_page_pdf_file_path)
            print(f"{pdf_file_name}: has odd number of pages ({number_of_pages}), appending empty page")
        writer.write(f"{dst_dir_path}/{pdf_file_name}")

def make_all_pdfs_even_number_of_pages(src_dir_path, dst_dir_path, empty_page_tmp_dir):
    pdfs_in_src_dir = list(Path(src_dir_path).glob('*.pdf'))
    is_first_file = True
    for pdf_file in pdfs_in_src_dir:
        if is_first_file:
            empty_page_pdf_file_path = create_empty_page(empty_page_tmp_dir, pdf_file)
        is_first_file = False
        make_even_pages_in_pdf_file(pdf_file, dst_dir_path, empty_page_pdf_file_path)

def merge_all_pdfs(src_dir_path, dst_pdf_file_path):
    pdfs_in_src_dir = list(Path(src_dir_path).glob('*.pdf'))
    print(f"Creating output PDF file: {dst_pdf_file_path}")
    with PdfWriter() as writer:
        for pdf_file in pdfs_in_src_dir:
            writer.append(pdf_file)
        writer.write(dst_pdf_file_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=Path, required=True, help="Input directory to glob pdfs in")
    parser.add_argument("--output_pdf", type=Path, required=True, help="Output pdf file path")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as empty_page_tmp_dir:
        with tempfile.TemporaryDirectory() as pdfs_tmp_dir:
            make_all_pdfs_even_number_of_pages(args.input_dir, pdfs_tmp_dir, empty_page_tmp_dir)
            merge_all_pdfs(pdfs_tmp_dir, args.output_pdf)
            print("Done! Thank you :)")


if __name__ == "__main__":
    main()
