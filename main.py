import os
import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QLineEdit,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont

from pdf.merge import merge_pdf
from pdf.split import split_pdf


class PDFDropList(QListWidget):
    """
    Satu widget yang berperan sebagai drop-zone SEKALIGUS daftar file.
    - Kosong  -> nampilin placeholder "Drop PDF di sini"
    - Ada isi -> nampilin daftar file, dan bisa di-drag reorder
    - Drop file baru dari luar (Finder/Explorer) -> otomatis ditambahin
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)  # drag utk reorder isi list
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setMinimumHeight(200)
        self.setSpacing(2)

        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #9a9a9a;
                border-radius: 12px;
                background-color: #fafafa;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 6px;
                margin: 2px 0px;
                border-bottom: 1px solid #e5e5e5;
                color: #333333;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #d9d9d9;
                color: black;
            }
        """)

    # --- terima drag file dari luar OS ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            main_window = self.window()

            for url in event.mimeData().urls():
                file = url.toLocalFile()

                if file.lower().endswith(".pdf"):
                    if file not in main_window.files:
                        main_window.files.append(file)
                        self.add_file_item(file)

            event.acceptProposedAction()
            self.viewport().update()

        else:
            # ini kasus reorder internal (drag antar item)
            super().dropEvent(event)
            self._sync_order_to_main_window()
            self.viewport().update()

    def add_file_item(self, filepath):
        """Tambah 1 baris item, nampilin nama file aja tapi simpan full path di data."""
        item = QListWidgetItem(os.path.basename(filepath))
        item.setToolTip(filepath)
        item.setData(Qt.UserRole, filepath)
        self.addItem(item)

    def _sync_order_to_main_window(self):
        main_window = self.window()
        main_window.files = [
            self.item(i).data(Qt.UserRole) for i in range(self.count())
        ]

    # --- placeholder digambar manual kalau list masih kosong ---
    def paintEvent(self, event):
        super().paintEvent(event)

        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#8a8a8a"))

            font = QFont()
            font.setPointSize(11)
            painter.setFont(font)

            rect = self.viewport().rect()
            painter.drawText(
                rect,
                Qt.AlignCenter,
                "Drop PDF di sini\natau klik \"Tambahkan PDF\"",
            )
            painter.end()


class PDFTool(QWidget):

    def __init__(self):
        super().__init__()

        self.files = []

        self.setWindowTitle("PDF Toolbox")
        self.setGeometry(500, 300, 480, 600)

        self.title = QLabel("PDF Toolbox")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #222222;
            padding: 4px 0 8px 0;
        """)

        # satu widget aja, gabungan drop area + list
        self.file_list = PDFDropList()

        self.select_btn = QPushButton("Tambahkan PDF")
        self.remove_btn = QPushButton("Hapus PDF Terpilih")
        self.merge_btn = QPushButton("Merge PDF")
        self.split_btn = QPushButton("Split PDF")

        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start Page")

        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("End Page")

        # --- styling monokrom, tanpa warna ---
        outline_btn_style = """
            QPushButton {
                background-color: white;
                color: #222222;
                border: 1px solid #b0b0b0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
            }
            QPushButton:pressed {
                background-color: #e2e2e2;
            }
        """

        solid_btn_style = """
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
        """

        self.select_btn.setStyleSheet(outline_btn_style)
        self.remove_btn.setStyleSheet(outline_btn_style)
        self.merge_btn.setStyleSheet(solid_btn_style)
        self.split_btn.setStyleSheet(solid_btn_style)

        input_style = """
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                color: #333333;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border: 1px solid #888888;
                background-color: white;
            }
        """
        self.start_input.setStyleSheet(input_style)
        self.end_input.setStyleSheet(input_style)

        for btn in (self.select_btn, self.remove_btn, self.merge_btn, self.split_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(40)

        self.select_btn.clicked.connect(self.select_pdf)
        self.remove_btn.clicked.connect(self.remove_pdf)
        self.merge_btn.clicked.connect(self.merge)
        self.split_btn.clicked.connect(self.split)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(10)

        layout.addWidget(self.title)
        layout.addWidget(self.file_list)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.remove_btn)
        layout.addSpacing(6)
        layout.addWidget(self.merge_btn)

        page_row = QHBoxLayout()
        page_row.setSpacing(10)
        page_row.addWidget(self.start_input)
        page_row.addWidget(self.end_input)
        layout.addLayout(page_row)

        layout.addWidget(self.split_btn)

        self.setLayout(layout)

    def select_pdf(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih PDF", "", "PDF Files (*.pdf)"
        )

        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_list.add_file_item(file)

        self.file_list.viewport().update()

    def remove_pdf(self):
        selected = self.file_list.currentRow()

        if selected >= 0:
            self.files.pop(selected)
            self.file_list.takeItem(selected)
            self.file_list.viewport().update()

    def merge(self):
        if len(self.files) < 2:
            QMessageBox.warning(self, "Error", "Pilih minimal 2 PDF")
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "Simpan PDF", "", "PDF (*.pdf)"
        )

        if output:
            merge_pdf(self.files, output)
            QMessageBox.information(self, "Sukses", "PDF berhasil digabung")

    def split(self):
        if len(self.files) != 1:
            QMessageBox.warning(self, "Error", "Pilih satu PDF saja")
            return

        try:
            start = int(self.start_input.text())
            end = int(self.end_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Masukkan nomor halaman")
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "Simpan PDF", "", "PDF (*.pdf)"
        )

        if output:
            split_pdf(self.files[0], start, end, output)
            QMessageBox.information(self, "Sukses", "PDF berhasil dipisah")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = PDFTool()
    window.show()

    sys.exit(app.exec())
