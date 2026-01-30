import os
import sys
import shutil
import subprocess
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QProgressBar, QScrollArea, QSplitter,
    QMainWindow, QStatusBar, QFrame, QGroupBox, QLineEdit, QTextEdit,
    QCheckBox, QSpinBox, QComboBox, QTabWidget, QMenu, QAction,
    QHeaderView, QAbstractItemView, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush

from UtilityFunctions import list_all_directories, process_batch, convert_path_format


class ScanWorker(QThread):
    """Background thread for scanning directories."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, folder_path, options=None):
        super().__init__()
        self.folder_path = folder_path
        self.options = options or {}

    def run(self):
        try:
            self.progress.emit("Converting path format...")
            folder_path = convert_path_format.convert_path_format(self.folder_path)

            self.progress.emit(f"Listing directories in '{folder_path}'...")
            list_all_directories.process_directories(folder_path)

            output_folder = os.path.join(folder_path, 'Seeker_Output/file_batches')
            if not os.path.exists(output_folder):
                self.error.emit(f"Output folder '{output_folder}' does not exist.")
                return

            self.progress.emit("Processing batch files...")
            batch_files = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]
            
            for i, batch_file in enumerate(batch_files):
                batch_file_path = os.path.join(output_folder, batch_file)
                self.progress.emit(f"Processing batch {i+1}/{len(batch_files)}: {batch_file}")
                process_batch.process_batch(batch_file_path)

            seeker_output = os.path.join(folder_path, 'Seeker_Output')
            self.finished.emit(seeker_output)

        except Exception as e:
            self.error.emit(str(e))


class ScanOptionsDialog(QDialog):
    """Dialog for configuring scan options."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Options")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # File size filter
        self.min_size = QSpinBox()
        self.min_size.setRange(0, 1000000)
        self.min_size.setValue(0)
        self.min_size.setSuffix(" KB")
        form.addRow("Minimum file size:", self.min_size)
        
        self.max_size = QSpinBox()
        self.max_size.setRange(0, 1000000)
        self.max_size.setValue(0)
        self.max_size.setSpecialValueText("No limit")
        self.max_size.setSuffix(" MB")
        form.addRow("Maximum file size:", self.max_size)
        
        # Extension filter
        self.extensions_filter = QLineEdit()
        self.extensions_filter.setPlaceholderText("e.g., .jpg,.png,.pdf (leave empty for all)")
        form.addRow("Include extensions:", self.extensions_filter)
        
        self.exclude_extensions = QLineEdit()
        self.exclude_extensions.setPlaceholderText("e.g., .tmp,.log,.bak")
        form.addRow("Exclude extensions:", self.exclude_extensions)
        
        # Other options
        self.skip_hidden = QCheckBox("Skip hidden files/folders")
        self.skip_hidden.setChecked(True)
        form.addRow(self.skip_hidden)
        
        self.skip_system = QCheckBox("Skip system folders")
        self.skip_system.setChecked(True)
        form.addRow(self.skip_system)
        
        self.follow_symlinks = QCheckBox("Follow symbolic links")
        self.follow_symlinks.setChecked(False)
        form.addRow(self.follow_symlinks)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_options(self):
        return {
            'min_size': self.min_size.value() * 1024,
            'max_size': self.max_size.value() * 1024 * 1024 if self.max_size.value() > 0 else None,
            'include_extensions': [e.strip() for e in self.extensions_filter.text().split(',') if e.strip()],
            'exclude_extensions': [e.strip() for e in self.exclude_extensions.text().split(',') if e.strip()],
            'skip_hidden': self.skip_hidden.isChecked(),
            'skip_system': self.skip_system.isChecked(),
            'follow_symlinks': self.follow_symlinks.isChecked()
        }


class StatisticsWidget(QWidget):
    """Widget displaying scan statistics."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Stats grid
        self.stats_layout = QHBoxLayout()
        
        self.total_files_label = self._create_stat_card("Total Files", "0")
        self.duplicate_files_label = self._create_stat_card("Duplicate Files", "0")
        self.wasted_space_label = self._create_stat_card("Wasted Space", "0 B")
        self.unique_hashes_label = self._create_stat_card("Unique Hashes", "0")
        
        self.stats_layout.addWidget(self.total_files_label)
        self.stats_layout.addWidget(self.duplicate_files_label)
        self.stats_layout.addWidget(self.wasted_space_label)
        self.stats_layout.addWidget(self.unique_hashes_label)
        
        layout.addLayout(self.stats_layout)
        
        # Extension breakdown
        self.extension_breakdown = QTableWidget()
        self.extension_breakdown.setColumnCount(4)
        self.extension_breakdown.setHorizontalHeaderLabels(["Extension", "Files", "Duplicates", "Wasted Space"])
        self.extension_breakdown.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(QLabel("Extension Breakdown:"))
        layout.addWidget(self.extension_breakdown)
    
    def _create_stat_card(self, title, value):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11px; color: #6c757d; font-weight: normal;")
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4a235a;")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return frame
    
    def update_stats(self, data):
        """Update statistics from scan data."""
        if data is None or data.empty:
            return
        
        total_files = len(data)
        duplicate_files = 0
        wasted = 0
        unique_hashes = 0
        
        # Count duplicates (files with same hash appearing more than once)
        hash_col = None
        for col in data.columns:
            if 'hash' in col.lower() or 'md5' in col.lower():
                hash_col = col
                break
        
        size_col = None
        for col in data.columns:
            if 'size' in col.lower():
                size_col = col
                break
        
        if hash_col:
            hash_counts = data[hash_col].value_counts()
            duplicate_hashes = hash_counts[hash_counts > 1]
            duplicate_files = int(duplicate_hashes.sum() - len(duplicate_hashes))
            unique_hashes = data[hash_col].nunique()
            
            if size_col:
                for hash_val, count in duplicate_hashes.items():
                    try:
                        file_size = pd.to_numeric(data[data[hash_col] == hash_val][size_col].iloc[0], errors='coerce')
                        if pd.notna(file_size):
                            wasted += file_size * (count - 1)
                    except:
                        pass
        
        wasted_str = self._format_size(wasted)
        
        # Update labels
        self._update_stat_value(self.total_files_label, str(total_files))
        self._update_stat_value(self.duplicate_files_label, str(duplicate_files))
        self._update_stat_value(self.wasted_space_label, wasted_str)
        self._update_stat_value(self.unique_hashes_label, str(unique_hashes))
    
    def _update_stat_value(self, frame, value):
        for child in frame.findChildren(QLabel):
            if child.objectName().endswith('_value'):
                child.setText(value)
                break
    
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


class ExtensionViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cluster Seeker - Duplicate File Finder")
        self.resize(1400, 1000)

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
            QPushButton#dangerBtn {{
                background-color: #c0392b;
            }}
            QPushButton#dangerBtn:hover {{
                background-color: #a93226;
            }}
            QPushButton#successBtn {{
                background-color: #27ae60;
            }}
            QPushButton#successBtn:hover {{
                background-color: #1e8449;
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
            QTabWidget::pane {{
                border: 1px solid {self.purple_light};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {self.purple_light};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.purple_medium};
                color: white;
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

        self.options_btn = QPushButton("⚙️ Options")
        self.options_btn.setMaximumWidth(100)
        self.options_btn.clicked.connect(self.show_scan_options)
        self.folder_select_layout.addWidget(self.options_btn)

        self.scan_btn = QPushButton("🔍 Start Scan")
        self.scan_btn.setMaximumWidth(120)
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        self.folder_select_layout.addWidget(self.scan_btn)

        self.scan_layout.addLayout(self.folder_select_layout)

        # Scan log output
        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        self.scan_log.setMaximumHeight(100)
        self.scan_log.setPlaceholderText("Scan progress will appear here...")
        self.scan_layout.addWidget(self.scan_log)

        # Scan progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        self.scan_progress.setRange(0, 0)
        self.scan_layout.addWidget(self.scan_progress)

        self.layout.addWidget(self.scan_group)

        # ============ STEP 2: Results Section with Tabs ============
        self.results_group = QGroupBox("Step 2: View & Manage Results")
        self.results_layout = QVBoxLayout(self.results_group)

        # Top section with load button and search
        self.top_section = QFrame()
        self.top_layout = QHBoxLayout(self.top_section)
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.folder_btn = QPushButton("📂 Load Results Folder")
        self.folder_btn.setMinimumHeight(36)
        self.folder_btn.clicked.connect(self.load_folder)
        self.top_layout.addWidget(self.folder_btn)

        self.output_path_label = QLabel("")
        self.output_path_label.setStyleSheet("font-weight: normal; color: #666;")
        self.top_layout.addWidget(self.output_path_label, 1)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search files...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.filter_table)
        self.top_layout.addWidget(self.search_input)

        self.results_layout.addWidget(self.top_section)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Tab 1: Data Browser
        self.browser_tab = QWidget()
        self.browser_layout = QHBoxLayout(self.browser_tab)
        
        # Left panel - Extensions list
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.extensions_label = QLabel("📄 Extensions:")
        self.left_layout.addWidget(self.extensions_label)

        self.extensions_list = QListWidget()
        self.extensions_list.setSelectionMode(QListWidget.MultiSelection)
        self.extensions_list.setMaximumWidth(200)
        self.left_layout.addWidget(self.extensions_list)

        # Quick select buttons
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_extensions)
        self.left_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_extension_selection)
        self.left_layout.addWidget(self.clear_selection_btn)

        self.load_btn = QPushButton("📊 Load Selected")
        self.load_btn.clicked.connect(self.load_selected_extensions)
        self.left_layout.addWidget(self.load_btn)

        self.browser_layout.addWidget(self.left_panel)

        # Right panel - Data table
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.table_label = QLabel("Data View:")
        self.right_layout.addWidget(self.table_label)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setSortingEnabled(True)
        self.right_layout.addWidget(self.table)

        self.browser_layout.addWidget(self.right_panel)
        self.tab_widget.addTab(self.browser_tab, "📁 File Browser")

        # Tab 2: Statistics
        self.stats_widget = StatisticsWidget()
        self.tab_widget.addTab(self.stats_widget, "📊 Statistics")

        # Tab 3: Duplicate Groups
        self.duplicates_tab = QWidget()
        self.duplicates_layout = QVBoxLayout(self.duplicates_tab)
        
        self.duplicates_table = QTableWidget()
        self.duplicates_table.setColumnCount(5)
        self.duplicates_table.setHorizontalHeaderLabels(["Hash", "Count", "Total Size", "Wasted Space", "Action"])
        self.duplicates_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.duplicates_table.horizontalHeader().setStretchLastSection(True)
        self.duplicates_layout.addWidget(self.duplicates_table)
        
        self.tab_widget.addTab(self.duplicates_tab, "🔄 Duplicate Groups")

        self.results_layout.addWidget(self.tab_widget)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.results_layout.addWidget(self.progress_bar)

        # Action buttons row
        self.action_layout = QHBoxLayout()

        self.export_btn = QPushButton("💾 Export to Excel")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        self.action_layout.addWidget(self.export_btn)

        self.export_csv_btn = QPushButton("📄 Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setEnabled(False)
        self.action_layout.addWidget(self.export_csv_btn)

        self.action_layout.addStretch()

        self.move_duplicates_btn = QPushButton("📦 Move Duplicates")
        self.move_duplicates_btn.setObjectName("successBtn")
        self.move_duplicates_btn.clicked.connect(self.move_duplicates)
        self.move_duplicates_btn.setEnabled(False)
        self.action_layout.addWidget(self.move_duplicates_btn)

        self.delete_duplicates_btn = QPushButton("🗑️ Delete Duplicates")
        self.delete_duplicates_btn.setObjectName("dangerBtn")
        self.delete_duplicates_btn.clicked.connect(self.delete_duplicates)
        self.delete_duplicates_btn.setEnabled(False)
        self.action_layout.addWidget(self.delete_duplicates_btn)

        self.results_layout.addLayout(self.action_layout)

        self.layout.addWidget(self.results_group)

        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready - Select a folder to scan or load existing results")

        # Set data members
        self.folder_path = None
        self.scan_folder_path = None
        self.scan_options = {}
        self.all_data = None
        self.filtered_data = None
        self.extension_to_dfs = {}
        self.xlsx_files = []
        self.current_file_index = 0
        self.scan_worker = None

    def show_scan_options(self):
        """Show scan options dialog."""
        dialog = ScanOptionsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.scan_options = dialog.get_options()
            self.log_scan("Scan options updated")

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
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.scan_log.append(f"[{timestamp}] {message}")
        scrollbar = self.scan_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_scan(self):
        """Start scanning the selected folder."""
        if not self.scan_folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder to scan first.")
            return

        self.scan_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.scan_progress.setVisible(True)
        self.scan_log.clear()
        self.log_scan(f"Starting scan of: {self.scan_folder_path}")

        self.scan_worker = ScanWorker(self.scan_folder_path, self.scan_options)
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
        
        self.log_scan("✅ Scan complete!")
        self.log_scan(f"Output saved to: {output_folder}")
        self.statusBar.showMessage("Scan complete!")

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
                item = QListWidgetItem(f"{ext} ({sum(len(df) for df in self.extension_to_dfs[ext])} files)")
                item.setData(Qt.UserRole, ext)
                item.setCheckState(Qt.Unchecked)
                self.extensions_list.addItem(item)
            self.statusBar.showMessage(f"Found {self.extensions_list.count()} extensions")
            self.enable_action_buttons()
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

    def enable_action_buttons(self):
        """Enable action buttons after data is loaded."""
        has_data = bool(self.extension_to_dfs)
        self.export_btn.setEnabled(has_data)
        self.export_csv_btn.setEnabled(has_data)
        self.move_duplicates_btn.setEnabled(has_data)
        self.delete_duplicates_btn.setEnabled(has_data)

    def select_all_extensions(self):
        """Select all extensions in the list."""
        for i in range(self.extensions_list.count()):
            self.extensions_list.item(i).setCheckState(Qt.Checked)

    def clear_extension_selection(self):
        """Clear all extension selections."""
        for i in range(self.extensions_list.count()):
            self.extensions_list.item(i).setCheckState(Qt.Unchecked)

    def load_selected_extensions(self):
        selected = []
        for i in range(self.extensions_list.count()):
            item = self.extensions_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))

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
        self.all_data = combined_df
        self.filtered_data = combined_df
        self.display_data(combined_df)
        self.stats_widget.update_stats(combined_df)
        self.update_duplicates_tab(combined_df)
        self.statusBar.showMessage(f"Loaded {len(combined_df)} rows of data")

    def filter_table(self, text):
        """Filter table based on search text."""
        if self.all_data is None:
            return
        
        if not text:
            self.filtered_data = self.all_data
        else:
            mask = self.all_data.astype(str).apply(lambda x: x.str.contains(text, case=False, na=False)).any(axis=1)
            self.filtered_data = self.all_data[mask]
        
        self.display_data(self.filtered_data)
        self.statusBar.showMessage(f"Showing {len(self.filtered_data)} of {len(self.all_data)} rows")

    def display_data(self, df):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.astype(str))
        self.table.setRowCount(len(df))

        for i in range(len(df)):
            for j in range(len(df.columns)):
                val = str(df.iat[i, j])
                item = QTableWidgetItem(val)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    def update_duplicates_tab(self, df):
        """Update the duplicates tab with grouped data."""
        self.duplicates_table.setRowCount(0)
        
        # Find hash column
        hash_col = None
        for col in df.columns:
            if 'hash' in col.lower() or 'md5' in col.lower():
                hash_col = col
                break
        
        if not hash_col:
            return
        
        # Find size column
        size_col = None
        for col in df.columns:
            if 'size' in col.lower():
                size_col = col
                break
        
        hash_counts = df[hash_col].value_counts()
        duplicate_hashes = hash_counts[hash_counts > 1]
        
        self.duplicates_table.setRowCount(len(duplicate_hashes))
        
        for i, (hash_val, count) in enumerate(duplicate_hashes.items()):
            hash_display = str(hash_val)[:16] + "..." if len(str(hash_val)) > 16 else str(hash_val)
            self.duplicates_table.setItem(i, 0, QTableWidgetItem(hash_display))
            self.duplicates_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
            if size_col:
                try:
                    file_size = pd.to_numeric(df[df[hash_col] == hash_val][size_col].iloc[0], errors='coerce')
                    if pd.notna(file_size):
                        total_size = file_size * count
                        wasted = file_size * (count - 1)
                        self.duplicates_table.setItem(i, 2, QTableWidgetItem(self._format_size(total_size)))
                        self.duplicates_table.setItem(i, 3, QTableWidgetItem(self._format_size(wasted)))
                    else:
                        self.duplicates_table.setItem(i, 2, QTableWidgetItem("N/A"))
                        self.duplicates_table.setItem(i, 3, QTableWidgetItem("N/A"))
                except:
                    self.duplicates_table.setItem(i, 2, QTableWidgetItem("N/A"))
                    self.duplicates_table.setItem(i, 3, QTableWidgetItem("N/A"))
            
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, h=hash_val, hc=hash_col: self.view_duplicate_group(h, hc))
            self.duplicates_table.setCellWidget(i, 4, view_btn)

    def view_duplicate_group(self, hash_val, hash_col):
        """Filter table to show only files with specific hash."""
        if self.all_data is None:
            return
        
        self.search_input.setText("")
        filtered = self.all_data[self.all_data[hash_col] == hash_val]
        self.filtered_data = filtered
        self.display_data(filtered)
        self.tab_widget.setCurrentIndex(0)
        hash_display = str(hash_val)[:16] + "..." if len(str(hash_val)) > 16 else str(hash_val)
        self.statusBar.showMessage(f"Showing {len(filtered)} files with hash {hash_display}")

    def show_context_menu(self, position):
        """Show context menu for table rows."""
        menu = QMenu()
        
        open_location_action = QAction("📂 Open File Location", self)
        open_location_action.triggered.connect(self.open_file_location)
        menu.addAction(open_location_action)
        
        open_file_action = QAction("📄 Open File", self)
        open_file_action.triggered.connect(self.open_selected_file)
        menu.addAction(open_file_action)
        
        menu.addSeparator()
        
        copy_path_action = QAction("📋 Copy Path", self)
        copy_path_action.triggered.connect(self.copy_file_path)
        menu.addAction(copy_path_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ Delete File", self)
        delete_action.triggered.connect(self.delete_selected_file)
        menu.addAction(delete_action)
        
        menu.exec_(self.table.mapToGlobal(position))

    def get_selected_file_path(self):
        """Get the file path from selected row."""
        selected = self.table.selectedItems()
        if not selected:
            return None
        
        row = selected[0].row()
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text().lower()
            if 'path' in header or 'file' in header:
                return self.table.item(row, col).text()
        return None

    def open_file_location(self):
        """Open the folder containing the selected file."""
        path = self.get_selected_file_path()
        if path and os.path.exists(path):
            subprocess.run(['explorer', '/select,', path])
        else:
            QMessageBox.warning(self, "Error", "Could not find file path.")

    def open_selected_file(self):
        """Open the selected file with default application."""
        path = self.get_selected_file_path()
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "Error", "Could not find file.")

    def copy_file_path(self):
        """Copy file path to clipboard."""
        path = self.get_selected_file_path()
        if path:
            QApplication.clipboard().setText(path)
            self.statusBar.showMessage("Path copied to clipboard")

    def delete_selected_file(self):
        """Delete the selected file."""
        path = self.get_selected_file_path()
        if not path:
            QMessageBox.warning(self, "Error", "Could not find file path.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete:\n{path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(path)
                self.statusBar.showMessage(f"Deleted: {path}")
                row = self.table.currentRow()
                self.table.removeRow(row)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file:\n{e}")

    def move_duplicates(self):
        """Move duplicate files to a specified folder."""
        if self.all_data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        dest_folder = QFileDialog.getExistingDirectory(self, "Select Destination for Duplicates")
        if not dest_folder:
            return
        
        # Find hash and path columns
        hash_col = None
        path_col = None
        for col in self.all_data.columns:
            if 'hash' in col.lower() or 'md5' in col.lower():
                hash_col = col
            if 'path' in col.lower() or 'file' in col.lower():
                path_col = col
        
        if not hash_col or not path_col:
            QMessageBox.warning(self, "Error", "Data must contain hash and path columns.")
            return
        
        duplicates = self.all_data[self.all_data.duplicated(subset=[hash_col], keep='first')]
        
        reply = QMessageBox.question(
            self, "Confirm Move",
            f"This will move {len(duplicates)} duplicate files to:\n{dest_folder}\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        moved = 0
        errors = []
        for _, row in duplicates.iterrows():
            src = row[path_col]
            if os.path.exists(src):
                try:
                    filename = os.path.basename(src)
                    dest = os.path.join(dest_folder, filename)
                    counter = 1
                    while os.path.exists(dest):
                        name, ext = os.path.splitext(filename)
                        dest = os.path.join(dest_folder, f"{name}_{counter}{ext}")
                        counter += 1
                    shutil.move(src, dest)
                    moved += 1
                except Exception as e:
                    errors.append(f"{src}: {e}")
        
        msg = f"Moved {moved} files."
        if errors:
            msg += f"\n\n{len(errors)} errors occurred."
        QMessageBox.information(self, "Complete", msg)
        self.statusBar.showMessage(f"Moved {moved} duplicate files")

    def delete_duplicates(self):
        """Delete duplicate files (keeping originals)."""
        if self.all_data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return
        
        # Find hash and path columns
        hash_col = None
        path_col = None
        for col in self.all_data.columns:
            if 'hash' in col.lower() or 'md5' in col.lower():
                hash_col = col
            if 'path' in col.lower() or 'file' in col.lower():
                path_col = col
        
        if not hash_col or not path_col:
            QMessageBox.warning(self, "Error", "Data must contain hash and path columns.")
            return
        
        duplicates = self.all_data[self.all_data.duplicated(subset=[hash_col], keep='first')]
        
        reply = QMessageBox.warning(
            self, "⚠️ Confirm Delete",
            f"This will PERMANENTLY DELETE {len(duplicates)} duplicate files!\n\n"
            "This action cannot be undone.\n\nAre you absolutely sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        reply2 = QMessageBox.warning(
            self, "⚠️ Final Confirmation",
            "This is your last chance to cancel.\n\nDelete all duplicates?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply2 != QMessageBox.Yes:
            return
        
        deleted = 0
        errors = []
        for _, row in duplicates.iterrows():
            path = row[path_col]
            if os.path.exists(path):
                try:
                    os.remove(path)
                    deleted += 1
                except Exception as e:
                    errors.append(f"{path}: {e}")
        
        msg = f"Deleted {deleted} files."
        if errors:
            msg += f"\n\n{len(errors)} errors occurred."
        QMessageBox.information(self, "Complete", msg)
        self.statusBar.showMessage(f"Deleted {deleted} duplicate files")

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

    def export_csv(self):
        if self.all_data is not None:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "merged_extensions.csv", "CSV Files (*.csv)")
            if path:
                try:
                    self.all_data.to_csv(path, index=False)
                    QMessageBox.information(self, "Exported", f"Data exported successfully to:\n{path}")
                    self.statusBar.showMessage(f"Data exported to {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export data:\n{e}")

    def _format_size(self, size_bytes):
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ExtensionViewer()
    viewer.show()
    sys.exit(app.exec_())
