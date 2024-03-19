#!.env/doc_merge/Scripts/pythonw

import sys
import traceback
from pathlib import Path
from DocMerger.doc_merger import DocMerger, ProgressLogIf
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QFileDialog,
    QSpinBox,
    QMessageBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QColorConstants, QIcon


class DummyProgressLog(ProgressLogIf):
    def __init__(self):
        self._max = 0
        self._cnt = 0


class DocMergeWorker(QThread, ProgressLogIf):
    progress_updated = pyqtSignal(int)
    detailed_output_updated = pyqtSignal(str)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str, str)

    def __init__(self, input_dir: Path, output_file: Path, align: int) -> None:
        super().__init__()
        self._input_dir = input_dir
        self._output_file = output_file
        self._align = align
        self._progress_bar_max = 0
        self._progress_bar_value = 0

    def run(self):
        try:
            DocMerger(self._input_dir, self._output_file, self._align, self).execute()
        except BaseException:
            ex_type, ex_value, _ = sys.exc_info()
            ex_traceback = traceback.format_exc()
            self.error_occurred.emit(ex_type.__name__, str(ex_value), ex_traceback)

    def init(self, max: int):
        self._progress_bar_max = max
        self._progress_bar_value = 0
        self.progress_updated.emit(0)

    def next(self):
        self._progress_bar_value += 1
        proc = int(round(self._progress_bar_value * 100 / self._progress_bar_max, 0))
        self.progress_updated.emit(proc)

    def finish(self):
        result = "Done! Thank you :)"
        self.msg(result)
        self.finished.emit(result)

    def msg(self, msg):
        self.detailed_output_updated.emit(msg)


class DocMergeGui(QMainWindow, ProgressLogIf):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Documents Merge Tool by Dominik Kała - v0.1.0")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("icon.ico"))

        self.initUI()

    def initUI(self):
        # Input directory
        self.input_dir_label = QLabel("Input directory:", self)
        self.input_dir_label.move(20, 20)
        self.input_dir_entry = QLineEdit(self)
        self.input_dir_entry.setGeometry(150, 20, 300, 25)
        self.browse_input_button = QPushButton("Browse", self)
        self.browse_input_button.setGeometry(470, 20, 100, 25)
        self.browse_input_button.clicked.connect(self.browse_input_dir)

        # Output PDF file
        self.output_file_label = QLabel("Output PDF file:", self)
        self.output_file_label.move(20, 60)
        self.output_file_entry = QLineEdit(self)
        self.output_file_entry.setGeometry(150, 60, 300, 25)
        self.browse_output_button = QPushButton("Browse", self)
        self.browse_output_button.setGeometry(470, 60, 100, 25)
        self.browse_output_button.clicked.connect(self.browse_output_file)

        # Align
        self.align_label = QLabel("Align:", self)
        self.align_label.move(20, 100)
        self.align_entry = QSpinBox(self)
        self.align_entry.setGeometry(150, 100, 50, 25)
        self.align_entry.setRange(2, 16)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, 140, 550, 20)

        # Detailed output
        self.detailed_output_label = QLabel("Detailed output:", self)
        self.detailed_output_label.move(20, 180)
        self.detailed_output_text = QTextEdit(self)
        self.detailed_output_text.setGeometry(20, 210, 550, 120)

        # Start conversion button
        self.start_merge = QPushButton("Start", self)
        self.start_merge.setGeometry(230, 350, 140, 30)
        self.start_merge.clicked.connect(self.start_conversion)
        self.clear_results()

    def browse_input_dir(self):
        input_dir = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        self.input_dir_entry.setText(input_dir)

    def browse_output_file(self):
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save Output PDF File", "", "PDF Files (*.pdf)"
        )
        self.output_file_entry.setText(output_file)

    def start_conversion(self):
        input_dir = Path(self.input_dir_entry.text())
        output_file = Path(self.output_file_entry.text())
        align_value = int(self.align_entry.text())

        # Clear output
        self.clear_results()

        # Add your conversion logic here
        self.worker_thread = DocMergeWorker(input_dir, output_file, align_value)
        self.worker_thread.progress_updated.connect(self.on_progress_update)
        self.worker_thread.detailed_output_updated.connect(
            self.on_detailed_output_update
        )
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.error_occurred.connect(self.on_error)
        self.worker_thread.start()

    def clear_results(self):
        self.progress_bar.setValue(0)
        self.detailed_output_text.clear()
        self.detailed_output_text.setTextColor(QColorConstants.Black)

    def on_progress_update(self, proc: int):
        self.progress_bar.setValue(proc)

    def on_detailed_output_update(self, msg: str):
        self.detailed_output_text.append(msg)

    def on_finished(self, msg: str):
        QMessageBox.information(self, "Finished", msg)

    def on_error(self, ex_type: str, ex_msg: str, ex_traceback: str):
        self.detailed_output_text.setTextColor(QColorConstants.Red)
        self.detailed_output_text.append(ex_traceback)
        self.detailed_output_text.setTextColor(QColorConstants.Black)
        QMessageBox.critical(self, "Error", f"{ex_type}: {ex_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    merger_app = DocMergeGui()
    merger_app.show()
    sys.exit(app.exec_())
