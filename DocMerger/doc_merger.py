from abc import abstractclassmethod
from pathlib import Path
from pdfreader import PDFDocument
from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from functools import partialmethod
from tqdm import tqdm

import docx2pdf
import tempfile
import time


class Tools:
    def get_number_of_pages_in_pdf(self, pdf_file_path: Path) -> int:
        with open(pdf_file_path, "rb") as pdf:
            pdf_doc = PDFDocument(pdf)
            number_of_pages = len(list(pdf_doc.pages()))
            return number_of_pages

    def create_empty_page(
        self, src_pdf_file_path: Path, output_pdf_file_path: Path
    ) -> None:
        with open(src_pdf_file_path, "rb") as pdf:
            pdf_doc = PDFDocument(pdf)
            pdf_pages_list = list(pdf_doc.pages())
            pdf_mediabox = pdf_pages_list[-1].MediaBox
            pdf_pagesize = (pdf_mediabox[2], pdf_mediabox[3])
            empty_page_canvas = canvas.Canvas(
                output_pdf_file_path.as_posix(), pagesize=pdf_pagesize
            )
            empty_page_canvas.showPage()
            empty_page_canvas.save()


class DocumentToPdfConverter:
    def __init__(self):
        tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)
    def list_supported_files_in_dir(self, dir_path: Path) -> list[Path]:
        docxs_list = list(dir_path.glob("*.docx"))
        return docxs_list

    def convert(self, input_file_path: Path, output_file_path: Path) -> None:
        extension = input_file_path.suffix
        if extension == ".docx":
            docx2pdf.convert(input_file_path, output_file_path)
        else:
            raise RuntimeError(f"Invalid extension {extension}")


class ProgressLogIf:
    @abstractclassmethod
    def init(self, max: int):
        pass

    @abstractclassmethod
    def next(self):
        pass

    @abstractclassmethod
    def finish(self, duration_s: float):
        pass

    @abstractclassmethod
    def msg(self, msg: str):
        pass


class DummyProgressLog(ProgressLogIf):
    def __init__(self):
        self._max = 0
        self._cnt = 0

    def init(self, max: int):
        self._max = max
        self._cnt = 0

    def next(self):
        self._cnt += 1
        proc = round(self._cnt * 100 / self._max, 0)
        print(f"Progress: {proc}%")

    def finish(self, duration_s: float):
        print(f"Done in {duration_s}s! Thank you :)")

    def msg(self, msg):
        print(msg)


class DocMerger:
    def __init__(
        self,
        input_dir_path: Path,
        output_pdf_path: Path,
        align: int = 2,
        progress_log: ProgressLogIf = DummyProgressLog(),
    ) -> None:
        self._input_dir_path = input_dir_path
        self._output_pdf_path = output_pdf_path
        self._align = align
        self._progress_log = progress_log
        self._nopdf_converter = DocumentToPdfConverter()
        self._tools = Tools()
        self._clear_files_to_process()

    def execute(self):
        start_time_s = time.monotonic()
        self._enumerate_files_to_process()
        self._init_progress_log()

        if len(self._pdf_files) == 0 and len(self._nopdf_files) == 0:
            self._progress_log.msg(
                "No files to merge, check if input path is valid and contain supported file types!"
            )
        else:
            self._exec()

        duration_s = round(time.monotonic() - start_time_s, 3)
        self._progress_log.finish(duration_s)
        self._clear_files_to_process()

    def _enumerate_files_to_process(self):
        self._nopdf_files = self._nopdf_converter.list_supported_files_in_dir(
            self._input_dir_path
        )
        self._pdf_files = list(self._input_dir_path.glob("*.pdf"))

    def _clear_files_to_process(self):
        self._nopdf_files = []
        self._pdf_files = []

    def _init_progress_log(self):
        pdfs_num = len(self._pdf_files)
        nopdfs_num = len(self._nopdf_files)
        OPERATIONS_NUM_PER_PDF = 2  # align pages, append to the file
        OPERATIONS_NUM_PER_NOPDF = 3  # 1 for convert to pdf + OPERATIONS_NUM_PER_PDF
        SAVE_MERGED_FILE_OPERATIONS_NUM = 1
        total_operations_num = (
            pdfs_num * OPERATIONS_NUM_PER_PDF
            + nopdfs_num * OPERATIONS_NUM_PER_NOPDF
            + SAVE_MERGED_FILE_OPERATIONS_NUM
        )
        self._progress_log.init(total_operations_num)

    def _exec(self):
        with tempfile.TemporaryDirectory() as aligned_pdfs_dir:
            aligned_pdfs_dir_path = Path(aligned_pdfs_dir)
            if len(self._nopdf_files) > 0:
                self._align_pages_num_nopdf_list(
                    self._nopdf_files, aligned_pdfs_dir_path
                )
            if len(self._pdf_files) > 0:
                self._align_pages_num_pdf_list(self._pdf_files, aligned_pdfs_dir_path)
            self._merge_pdfs(aligned_pdfs_dir_path)

    def _align_pages_num_nopdf_list(
        self, nopdf_file_paths: list[Path], output_dir_path: Path
    ):
        with tempfile.TemporaryDirectory() as converted_files_dir:
            converted_file_paths = []
            for nopdf_file_path in nopdf_file_paths:
                self._progress_log.msg(f"Converting to PDF: {nopdf_file_path.name}")
                converted_file_path = Path(
                    f"{converted_files_dir}/{nopdf_file_path.stem}.pdf"
                )
                self._nopdf_converter.convert(nopdf_file_path, converted_file_path)
                converted_file_paths.append(converted_file_path)
                self._progress_log.next()
            self._align_pages_num_pdf_list(converted_file_paths, output_dir_path)

    def _align_pages_num_pdf_list(
        self, pdf_file_paths: list[Path], output_dir_path: Path
    ):
        with tempfile.TemporaryDirectory() as empty_page_dir:
            for pdf_file_path in pdf_file_paths:
                output_pdf_file_path = Path(
                    f"{output_dir_path.as_posix()}/{pdf_file_path.name}"
                )
                empty_page_pdf_file_path = Path(f"{empty_page_dir}/empty.pdf")
                self._tools.create_empty_page(pdf_file_path, empty_page_pdf_file_path)
                self._align_pages_num_pdf(
                    pdf_file_path, output_pdf_file_path, empty_page_pdf_file_path
                )
                self._progress_log.next()

    def _align_pages_num_pdf(
        self,
        pdf_file_path: Path,
        output_pdf_file_path: Path,
        empty_page_pdf_file_path: Path,
    ):
        pages_num = self._tools.get_number_of_pages_in_pdf(pdf_file_path)
        remaining_pages = pages_num % self._align
        empty_pages_num_to_append = (self._align - remaining_pages) % self._align
        self._progress_log.msg(
            f"File has {pages_num} pages, adding {empty_pages_num_to_append} empty page(s): {pdf_file_path.name}"
        )
        with PdfWriter() as pdf_writer:
            pdf_writer.append(pdf_file_path)
            for _ in range(empty_pages_num_to_append):
                pdf_writer.append(empty_page_pdf_file_path)
            pdf_writer.write(output_pdf_file_path.as_posix())

    def _merge_pdfs(self, pdfs_input_dir: Path):
        pdfs_to_merge = list(pdfs_input_dir.glob("*pdf"))
        self._progress_log.msg(
            f"Creating output PDF file: {self._output_pdf_path.as_posix()}"
        )
        with PdfWriter() as pdf_writer:
            for pdf_file in pdfs_to_merge:
                self._progress_log.msg(f"Merging: {pdf_file.name}")
                pdf_writer.append(pdf_file)
                self._progress_log.next()
            pdf_writer.write(self._output_pdf_path.as_posix())
            self._progress_log.msg(f"Number of files merged: {len(pdfs_to_merge)}")
            self._progress_log.next()
