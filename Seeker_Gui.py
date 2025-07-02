import os
import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QProgressBar, QScrollArea, QSplitter,
    QMainWindow, QStatusBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

class ExtensionViewer(QMainWindow):  # Changed to QMainWindow for more features
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seeker Output Extension Viewer")
        self.resize(1200, 800)

        # Define purple theme colors
        self.purple_dark = "#4a235a"
        self.purple_medium = "#6c3483"
        self.purple_light = "#d2b4de"

        # Apply theme styling
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: white;
            }}
            QPushButton {{
                background-color: {self.purple_medium};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.purple_dark};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
            QTableWidget {{
                border: 1px solid {self.purple_light};
                gridline-color: {self.purple_light};
                selection-background-color: {self.purple_light};
            }}
            QHeaderView::section {{
                background-color: {self.purple_dark};
                color: white;
                padding: 4px;
                font-weight: bold;
            }}
            QListWidget {{
                border: 1px solid {self.purple_light};
            }}
            QProgressBar {{
                border: 1px solid {self.purple_light};
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.purple_medium};
                border-radius: 5px;
            }}
            QLabel {{
                color: {self.purple_dark};
                font-weight: bold;
            }}
            QStatusBar {{
                background-color: {self.purple_dark};
                color: white;
            }}
        """)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # Top section with buttons
        self.top_section = QFrame()
        self.top_layout = QHBoxLayout(self.top_section)
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_btn = QPushButton("📁 Load Seeker_Output Folder")
        self.folder_btn.setMinimumHeight(36)
        self.folder_btn.clicked.connect(self.load_folder)
        self.top_layout.addWidget(self.folder_btn)

        self.layout.addWidget(self.top_section)

        # Create splitter for better UI organization
        self.splitter = QSplitter(Qt.Horizontal)

        # Left panel - Extensions list
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.extensions_label = QLabel("📄 Available Extensions:")
        self.left_layout.addWidget(self.extensions_label)

        self.extensions_list = QListWidget()
        self.extensions_list.setSelectionMode(QListWidget.MultiSelection)
        self.left_layout.addWidget(self.extensions_list)

        self.load_btn = QPushButton("📊 Load Selected Extensions")
        self.load_btn.clicked.connect(self.load_selected_extensions)
        self.left_layout.addWidget(self.load_btn)

        # Right panel - Data table
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.table_label = QLabel("Data View:")
        self.right_layout.addWidget(self.table_label)

        self.table = QTableWidget()
        self.right_layout.addWidget(self.table)

        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([300, 700])

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Add export button
        self.export_btn = QPushButton("💾 Export Displayed Data to Excel")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)

        # Add elements to main layout
        self.layout.addWidget(self.splitter)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.export_btn)

        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Set data members
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

        self.statusBar.showMessage(f"Loading {len(self.xlsx_files)} files...")
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
            self.statusBar.showMessage(f"Found {self.extensions_list.count()} extensions")
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
        self.statusBar.showMessage(f"Processing file {self.current_file_index} of {len(self.xlsx_files)}...")
        QTimer.singleShot(10, self.process_next_file)

    def load_selected_extensions(self):
        selected = [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]

        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one extension.")
            return

        self.statusBar.showMessage(f"Loading data for {len(selected)} extensions...")
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
        self.statusBar.showMessage(f"Loaded {len(combined_df)} rows of data")

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

        # Auto-resize columns for better viewing
        self.table.resizeColumnsToContents()

    def export_data(self):
        if self.all_data is not None:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "merged_extensions.xlsx", "Excel Files (*.xlsx)")
            if path:
                try:
                    self.all_data.to_excel(path, index=False)
                    QMessageBox.information(self, "Exported", f"Data exported successfully to:\n{path}")
                    self.statusBar.showMessage(f"Data exported to {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export data:\n{e}")
                    self.statusBar.showMessage("Export failed")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ExtensionViewer()
    viewer.show()
    sys.exit(app.exec_())
