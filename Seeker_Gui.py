import os
import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QProgressBar, QScrollArea, QSplitter,
    QMainWindow, QStatusBar, QFrame, QGroupBox, QLineEdit, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from UtilityFunctions import list_all_directories, process_batch, convert_path_format


class ScanWorker(QThread):
    """Background thread for scanning directories."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        try:
            # Convert path format if needed
            self.progress.emit(f"Converting path format...")
            folder_path = convert_path_format.convert_path_format(self.folder_path)

            # List and process directories
            self.progress.emit(f"Listing directories in '{folder_path}'...")
            list_all_directories.process_directories(folder_path)

            # Process batch files
            output_folder = os.path.join(folder_path, 'Seeker_Output/file_batches')
            if not os.path.exists(output_folder):
                self.error.emit(f"Output folder '{output_folder}' does not exist.")
                return

            self.progress.emit(f"Processing batch files...")
            batch_files = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]

            for i, batch_file in enumerate(batch_files):
                batch_file_path = os.path.join(output_folder, batch_file)
                self.progress.emit(f"Processing batch {i+1}/{len(batch_files)}: {batch_file}")
                process_batch.process_batch(batch_file_path)

            # Return the Seeker_Output folder path
            seeker_output = os.path.join(folder_path, 'Seeker_Output')
            self.finished.emit(seeker_output)

        except Exception as e:
            self.error.emit(str(e))


class ExtensionViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cluster Seeker - Duplicate File Finder")
        self.resize(1200, 900)

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
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.purple_light};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                color: {self.purple_dark};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QTextEdit {{
                border: 1px solid {self.purple_light};
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
            QLineEdit {{
                border: 1px solid {self.purple_light};
                border-radius: 4px;
                padding: 5px;
            }}
        """)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # ============ STEP 1: Scan Folder Section ============
        self.scan_group = QGroupBox("Step 1: Scan Folder for Duplicates")
        self.scan_layout = QVBoxLayout(self.scan_group)

        # Folder selection row
        self.folder_select_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select a folder to scan...")
        self.folder_input.setReadOnly(True)
        self.folder_select_layout.addWidget(self.folder_input)

        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setMaximumWidth(100)
        self.browse_btn.clicked.connect(self.browse_scan_folder)
        self.folder_select_layout.addWidget(self.browse_btn)

        self.scan_btn = QPushButton("🔍 Start Scan")
        self.scan_btn.setMaximumWidth(120)
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        self.folder_select_layout.addWidget(self.scan_btn)

        self.scan_layout.addLayout(self.folder_select_layout)

        # Scan log output
        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        self.scan_log.setMaximumHeight(120)
        self.scan_log.setPlaceholderText("Scan progress will appear here...")
        self.scan_layout.addWidget(self.scan_log)

        # Scan progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        self.scan_progress.setRange(0, 0)  # Indeterminate
        self.scan_layout.addWidget(self.scan_progress)

        self.layout.addWidget(self.scan_group)

        # ============ STEP 2: Load Results Section ============
        self.results_group = QGroupBox("Step 2: View Scan Results")
        self.results_layout = QVBoxLayout(self.results_group)

        # Top section with load button
        self.top_section = QFrame()
        self.top_layout = QHBoxLayout(self.top_section)
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_btn = QPushButton("📂 Load Seeker_Output Folder")
        self.folder_btn.setMinimumHeight(36)
        self.folder_btn.clicked.connect(self.load_folder)
        self.top_layout.addWidget(self.folder_btn)

        self.output_path_label = QLabel("")
        self.output_path_label.setStyleSheet("font-weight: normal; color: #666;")
        self.top_layout.addWidget(self.output_path_label, 1)

        self.results_layout.addWidget(self.top_section)

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

        self.results_layout.addWidget(self.splitter)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.results_layout.addWidget(self.progress_bar)

        # Add export button
        self.export_btn = QPushButton("💾 Export Displayed Data to Excel")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        self.results_layout.addWidget(self.export_btn)

        self.layout.addWidget(self.results_group)

        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready - Select a folder to scan or load existing results")

        # Set data members
        self.folder_path = None
        self.scan_folder_path = None
        self.all_data = None
        self.extension_to_dfs = {}
        self.xlsx_files = []
        self.current_file_index = 0
        self.scan_worker = None

    def browse_scan_folder(self):
        """Browse for a folder to scan."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.scan_folder_path = folder
            self.folder_input.setText(folder)
            self.scan_btn.setEnabled(True)
            self.log_scan(f"Selected folder: {folder}")

    def log_scan(self, message):
        """Add a message to the scan log."""
        self.scan_log.append(message)
        # Auto-scroll to bottom
        scrollbar = self.scan_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_scan(self):
        """Start scanning the selected folder."""
        if not self.scan_folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder to scan first.")
            return

        # Disable buttons during scan
        self.scan_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.scan_progress.setVisible(True)
        self.scan_log.clear()
        self.log_scan(f"Starting scan of: {self.scan_folder_path}")

        # Create and start worker thread
        self.scan_worker = ScanWorker(self.scan_folder_path)
        self.scan_worker.progress.connect(self.on_scan_progress)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def on_scan_progress(self, message):
        """Handle progress updates from scan worker."""
        self.log_scan(message)
        self.statusBar.showMessage(message)

    def on_scan_finished(self, output_folder):
        """Handle scan completion."""
        self.scan_progress.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

        self.log_scan(f"✅ Scan complete!")
        self.log_scan(f"Output saved to: {output_folder}")
        self.statusBar.showMessage("Scan complete!")

        # Ask user if they want to load the results
        reply = QMessageBox.question(
            self, "Scan Complete",
            f"Scan completed successfully!\n\nOutput folder:\n{output_folder}\n\nWould you like to load the results now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.load_folder_path(output_folder)

    def on_scan_error(self, error_message):
        """Handle scan errors."""
        self.scan_progress.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

        self.log_scan(f"❌ Error: {error_message}")
        self.statusBar.showMessage("Scan failed")
        QMessageBox.critical(self, "Scan Error", f"An error occurred during scanning:\n\n{error_message}")

    def load_folder(self):
        """Manually browse and load a Seeker_Output folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Seeker_Output Folder")
        if folder:
            self.load_folder_path(folder)

    def load_folder_path(self, folder_path):
        """Load a Seeker_Output folder by path."""
        self.folder_path = folder_path
        self.output_path_label.setText(f"📁 {folder_path}")

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
