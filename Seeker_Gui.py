import os
import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QProgressBar, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer

class ExtensionViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seeker Output Extension Viewer")
        self.resize(1000, 700)

        self.layout = QVBoxLayout()

        self.folder_btn = QPushButton("📁 Load Seeker_Output Folder")
        self.folder_btn.clicked.connect(self.load_folder)
        self.layout.addWidget(self.folder_btn)

        self.extensions_label = QLabel("📄 Available Extensions:")
        self.layout.addWidget(self.extensions_label)

        self.extensions_list = QListWidget()
        self.extensions_list.setSelectionMode(QListWidget.MultiSelection)
        self.layout.addWidget(self.extensions_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.load_btn = QPushButton("📊 Load Selected Extensions")
        self.load_btn.clicked.connect(self.load_selected_extensions)
        self.layout.addWidget(self.load_btn)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.export_btn = QPushButton("💾 Export Displayed Data to Excel")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        self.layout.addWidget(self.export_btn)

        self.setLayout(self.layout)

        self.folder_path = None
        self.all_data = None
        self.extension_to_dfs = {}
        self.xlsx_files = []
        self.current_file_index = 0

    def load_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Seeker_Output Folder")
        if not self.folder_path:
            return

        self.extensions_list.clear()
        self.extension_to_dfs.clear()
        self.xlsx_files = [f for f in os.listdir(self.folder_path) if f.endswith("_extensions.xlsx")]

        if not self.xlsx_files:
            QMessageBox.warning(self, "No Files", "No *_extensions.xlsx files found in the folder.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.xlsx_files))
        self.progress_bar.setValue(0)
        self.current_file_index = 0
        QTimer.singleShot(10, self.process_next_file)

    def process_next_file(self):
        if self.current_file_index >= len(self.xlsx_files):
            self.progress_bar.setVisible(False)
            for ext in sorted(self.extension_to_dfs):
                item = QListWidgetItem(ext)
                item.setCheckState(Qt.Unchecked)
                self.extensions_list.addItem(item)
            return

        file = self.xlsx_files[self.current_file_index]
        full_path = os.path.join(self.folder_path, file)
        try:
            xl = pd.ExcelFile(full_path)
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                self.extension_to_dfs.setdefault(sheet, []).append(df)
        except Exception as e:
            print(f"Failed to read {file}: {e}")

        self.current_file_index += 1
        self.progress_bar.setValue(self.current_file_index)
        QTimer.singleShot(10, self.process_next_file)

    def load_selected_extensions(self):
        selected = [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]

        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one extension.")
            return

        dfs = []
        for ext in selected:
            dfs.extend(self.extension_to_dfs.get(ext, []))

        if not dfs:
            QMessageBox.warning(self, "No Data", "No data found for selected extensions.")
            return

        combined_df = pd.concat(dfs, ignore_index=True)
        self.display_data(combined_df)
        self.all_data = combined_df
        self.export_btn.setEnabled(True)

    def display_data(self, df):
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.astype(str))
        self.table.setRowCount(len(df))

        for i in range(len(df)):
            for j in range(len(df.columns)):
                val = str(df.iat[i, j])
                self.table.setItem(i, j, QTableWidgetItem(val))

    def export_data(self):
        if self.all_data is not None:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "merged_extensions.xlsx", "Excel Files (*.xlsx)")
            if path:
                try:
                    self.all_data.to_excel(path, index=False)
                    QMessageBox.information(self, "Exported", f"Data exported successfully to:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export data:\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ExtensionViewer()
    viewer.show()
    sys.exit(app.exec_())
