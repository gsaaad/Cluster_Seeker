import sys
import os
import datetime # Added for file details
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                            QMessageBox, QTabWidget, QGroupBox, QStatusBar,
                            QTextEdit, QTreeView, QListWidget, QSplitter, # Added QTreeView, QListWidget, QSplitter
                            QAbstractItemView, QHeaderView, QLineEdit, # Added QAbstractItemView, QHeaderView, QLineEdit
                            QListWidgetItem) # Added QListWidgetItem
from PyQt5.QtCore import Qt, QIODevice, QDir # Added QDir
from PyQt5.QtGui import QIcon, QFont, QStandardItemModel, QStandardItem # Added QStandardItemModel, QStandardItem
from UtilityFunctions import list_all_directories, process_batch

class SeekerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seeker - File & Directory Explorer") # Updated Title
        self.setMinimumSize(800, 600) # Increased default size
        self.output_file_path = "Output/subdirectories.txt" # Define path for reuse
        self.current_selected_dir_path = None # To store path selected in tree

        # Set style sheet for modern dark theme (minor adjustments for new widgets)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QTabWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2D2D30;
                color: #FFFFFF;
                min-width: 100px;
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QLabel {
                color: #FFFFFF;
                padding: 5px;
            }
            QGroupBox {
                border: 1px solid #3E3E42;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #CCCCCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0px 5px;
            }
            QStatusBar {
                background-color: #007ACC;
                color: white;
            }
            QTextEdit, QListWidget, QTreeView { /* Apply style to new widgets */
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                padding: 5px;
            }
            QHeaderView::section { /* Style TreeView header */
                background-color: #2D2D30;
                color: #CCCCCC;
                padding: 4px;
                border: 1px solid #3E3E42;
            }
            QLineEdit { /* Style for search bar */
                 background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                padding: 5px;
            }
            QSplitter::handle { /* Style splitter handle */
                background-color: #3E3E42;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
        """)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Add status bar first, so it's available for tabs
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Create tab widget
        tab_widget = QTabWidget()

        # Create tabs
        local_tab = self.create_local_tab()
        output_tab = self.create_output_tab() # Create the new output tab

        # Add tabs to widget
        tab_widget.addTab(local_tab, "Local Seeker Actions") # Renamed tab
        tab_widget.addTab(output_tab, "Directory Explorer") # Renamed tab

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)

    def create_local_tab(self):
        # ... (Keep existing create_local_tab method as is) ...
        # ... existing code ...
        tab = QWidget()
        layout = QVBoxLayout()

        # List Directories Group
        list_group = QGroupBox("Directory Listing")
        list_layout = QVBoxLayout()

        list_description = QLabel("First, select directories to scan. This populates the 'Directory Explorer' tab with the structure found.")
        list_description.setWordWrap(True)
        list_layout.addWidget(list_description)

        list_btn = QPushButton("List Directories")
        list_btn.setIcon(QIcon.fromTheme("folder-open"))
        list_btn.clicked.connect(self.list_directories)
        list_layout.addWidget(list_btn)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Process Group
        process_group = QGroupBox("Process Files")
        process_layout = QVBoxLayout()

        process_description = QLabel("Select a folder or batch file (generated during listing) to process using Seeker's analysis functions.")
        process_description.setWordWrap(True)
        process_layout.addWidget(process_description)

        process_btn = QPushButton("Select Folder/File to Process")
        process_btn.setIcon(QIcon.fromTheme("document-open"))
        process_btn.clicked.connect(self.process_selection)
        process_layout.addWidget(process_btn)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        # Add spacer at bottom
        layout.addStretch()

        tab.setLayout(layout)
        return tab


    def create_output_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Top layout for search and refresh
        top_layout = QHBoxLayout()

        # Search/Filter Input
        self.filter_line_edit = QLineEdit()
        self.filter_line_edit.setPlaceholderText("Filter directories...")
        self.filter_line_edit.textChanged.connect(self.filter_directory_tree) # Connect filter
        top_layout.addWidget(self.filter_line_edit)

        # Refresh Button
        refresh_btn = QPushButton("Refresh View")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.load_directory_data) # Connect to reload data
        top_layout.addWidget(refresh_btn)

        layout.addLayout(top_layout)

        # Main Splitter (Tree | File List + Details)
        main_splitter = QSplitter(Qt.Horizontal)

        # Directory Tree View
        self.dir_tree_view = QTreeView()
        self.dir_model = QStandardItemModel()
        self.dir_tree_view.setModel(self.dir_model)
        self.dir_tree_view.setHeaderHidden(True) # Hide default header
        self.dir_tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers) # Make read-only
        self.dir_tree_view.clicked.connect(self.on_directory_selected) # Connect click signal
        main_splitter.addWidget(self.dir_tree_view)

        # Right Splitter (File List | Details)
        right_splitter = QSplitter(Qt.Vertical)

        # File List View
        self.file_list_widget = QListWidget()
        self.file_list_widget.currentItemChanged.connect(self.on_file_selected) # Connect selection change
        right_splitter.addWidget(self.file_list_widget)

        # File Details Area
        details_group = QGroupBox("File Details")
        details_layout = QVBoxLayout()
        self.details_text_edit = QTextEdit()
        self.details_text_edit.setReadOnly(True)
        details_layout.addWidget(self.details_text_edit)
        details_group.setLayout(details_layout)
        right_splitter.addWidget(details_group)

        # Adjust splitter sizes
        right_splitter.setSizes([200, 150]) # Initial sizes for file list and details

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([300, 450]) # Initial sizes for tree and right panel

        layout.addWidget(main_splitter)
        tab.setLayout(layout)

        self.load_directory_data() # Load initial data if file exists
        return tab

    def format_size(self, size_bytes):
        """Helper to format bytes into KB, MB, GB."""
        if size_bytes < 1024:
            return f"{size_bytes} Bytes"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/1024**2:.2f} MB"
        else:
            return f"{size_bytes/1024**3:.2f} GB"

    def on_directory_selected(self, index):
        """Populates the file list when a directory is clicked in the tree."""
        item = self.dir_model.itemFromIndex(index)
        if item and item.data(Qt.UserRole): # Check if it has path data
            dir_path = item.data(Qt.UserRole)
            self.current_selected_dir_path = dir_path # Store current path
            self.file_list_widget.clear()
            self.details_text_edit.clear()
            try:
                if os.path.isdir(dir_path):
                    for entry in os.listdir(dir_path):
                        full_path = os.path.join(dir_path, entry)
                        if os.path.isfile(full_path):
                            list_item = QListWidgetItem(entry)
                            # Store full path in the item for later retrieval
                            list_item.setData(Qt.UserRole, full_path)
                            self.file_list_widget.addItem(list_item)
                    self.statusBar.showMessage(f"Listed files in: {os.path.basename(dir_path)}", 3000)
                else:
                     self.statusBar.showMessage(f"Selected path is not a directory: {dir_path}", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Error listing files: {e}", 5000)
                self.details_text_edit.setText(f"Error listing files:\n{e}")
        else:
            self.current_selected_dir_path = None
            self.file_list_widget.clear()
            self.details_text_edit.clear()


    def on_file_selected(self, current_item, previous_item):
        """Displays details of the selected file."""
        if current_item:
            file_path = current_item.data(Qt.UserRole) # Retrieve full path
            if file_path and os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    details = []
                    details.append(f"File: {os.path.basename(file_path)}")
                    details.append(f"Path: {file_path}")
                    details.append(f"Size: {self.format_size(stat_info.st_size)}")
                    details.append(f"Created: {datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
                    details.append(f"Modified: {datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
                    details.append(f"Accessed: {datetime.datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')}")
                    self.details_text_edit.setPlainText("\n".join(details))
                except Exception as e:
                    self.details_text_edit.setText(f"Error getting file details:\n{e}")
                    self.statusBar.showMessage(f"Error getting details for {os.path.basename(file_path)}: {e}", 5000)
            else:
                 self.details_text_edit.setText("File not found or path invalid.")
        else:
            self.details_text_edit.clear()

    def load_directory_data(self):
        """Loads directory structure from Output/subdirectories.txt into the QTreeView."""
        self.dir_model.clear() # Clear existing model
        self.dir_model.setHorizontalHeaderLabels(['Directory Structure']) # Set header
        root_node = self.dir_model.invisibleRootItem()
        path_dict = {} # Keep track of items by path to build hierarchy

        try:
            if os.path.exists(self.output_file_path):
                with open(self.output_file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()] # Read non-empty lines

                if not lines:
                    root_node.appendRow(QStandardItem("No directories listed yet."))
                    self.statusBar.showMessage("Output file is empty.", 3000)
                    return

                # Sort lines to ensure parents are processed before children
                lines.sort()

                for path in lines:
                    if not os.path.isdir(path): # Skip if path no longer exists or isn't a dir
                        continue

                    parts = path.replace(os.sep, '/').split('/')
                    parent_item = root_node
                    current_path_str = ""

                    for i, part in enumerate(parts):
                        if not part: continue # Skip empty parts (e.g., from C:/)

                        # Handle drive letters correctly on Windows
                        if i == 0 and ':' in part:
                             current_path_str = part + '/'
                        elif i == 0: # Root directory on Unix-like
                             current_path_str = '/' + part
                        else:
                             current_path_str = os.path.join(current_path_str, part)

                        # Normalize path for dictionary key
                        normalized_path_key = os.path.normpath(current_path_str)

                        if normalized_path_key not in path_dict:
                            item = QStandardItem(part)
                            item.setData(normalized_path_key, Qt.UserRole) # Store full path
                            item.setIcon(QIcon.fromTheme("folder")) # Set folder icon
                            item.setEditable(False)
                            parent_item.appendRow(item)
                            path_dict[normalized_path_key] = item
                            parent_item = item # New parent for next part
                        else:
                            parent_item = path_dict[normalized_path_key] # Existing item becomes parent

                self.statusBar.showMessage("Directory structure loaded.", 3000)
                self.dir_tree_view.expandToDepth(0) # Expand top level
            else:
                root_node.appendRow(QStandardItem("Output file (subdirectories.txt) not found."))
                self.statusBar.showMessage("Output file not found.", 3000)
        except Exception as e:
            self.dir_model.clear()
            root_node.appendRow(QStandardItem(f"Error loading structure: {e}"))
            self.statusBar.showMessage(f"Error loading directory structure: {e}", 5000)
            QMessageBox.warning(self, "Load Error", f"Could not load or parse directory structure:\n{e}")

        # Clear file list and details when structure reloads
        self.file_list_widget.clear()
        self.details_text_edit.clear()
        self.current_selected_dir_path = None


    def filter_directory_tree(self, text):
        """Filters the directory tree view based on the input text."""
        # This is a basic filter - hides non-matching items.
        # More sophisticated filtering might require iterating differently.
        search_text = text.lower()
        root = self.dir_model.invisibleRootItem()
        for i in range(root.rowCount()):
            self.filter_recursive(root.child(i), search_text)

        # Expand items that have visible children after filtering
        # (This part can be complex to get perfect)
        # self.dir_tree_view.expandAll() # Simple approach: expand all after filter

    def filter_recursive(self, item, search_text):
        """Recursive helper for filtering tree items."""
        item_text = item.text().lower()
        # Check if the item itself matches
        matches_self = search_text in item_text

        # Recursively check children
        has_matching_child = False
        for i in range(item.rowCount()):
            child_item = item.child(i)
            if self.filter_recursive(child_item, search_text):
                has_matching_child = True

        # Set visibility based on self match or child match
        should_be_visible = matches_self or has_matching_child
        parent = item.parent()
        if parent: # Don't hide the invisible root
             # Get the QModelIndex for the item to use setRowHidden
             index = self.dir_model.indexFromItem(item)
             if index.isValid():
                 self.dir_tree_view.setRowHidden(index.row(), parent.index(), not should_be_visible)


        return should_be_visible


    def list_directories(self):
        # ... (Keep existing directory selection logic) ...
        # ... existing code ...
        output_folder = "Output/file_batches"
        selected_directories = []

        # Create Output directories if they don't exist
        os.makedirs("Output", exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        while True:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan") # Updated title
            if directory:
                selected_directories.append(directory)
                # Create a QMessageBox instance to allow styling
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setWindowTitle("Continue Scanning")
                msg_box.setText("Do you want to select another directory to scan?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                # Apply stylesheet for black text
                msg_box.setStyleSheet("QLabel { color: black; }") # Sets the text color of the label inside the message box
                continue_dialog = msg_box.exec_()
                if continue_dialog == QMessageBox.No:
                    break
            else: # User cancelled the dialog
                # If they cancelled the *first* dialog, don't proceed
                if not selected_directories:
                    self.statusBar.showMessage("Directory selection cancelled.")
                    return
                break # Break if they cancelled after selecting at least one

        if selected_directories:
            print("Selected directories for scanning:", selected_directories)
            # Create a QMessageBox instance to allow styling
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Scanning Directories")
            msg_box.setText("Scanning the following directories:\n" + "\n".join(selected_directories) + "\n\nResults will appear in the 'Directory Explorer' tab.")
            # Apply stylesheet for black text
            msg_box.setStyleSheet("QLabel { color: black; }") # Sets the text color of the label inside the message box
            msg_box.exec_()
            self.statusBar.showMessage("Scanning directories...")
            QApplication.processEvents() # Update UI

            try:
                # Run list_all_directories on the selected directories
                # This function is expected to write to self.output_file_path
                list_all_directories.process_directories(selected_directories, self.output_file_path, output_folder)
                self.statusBar.showMessage("Directory scanning complete! Refreshing view...")
                self.load_directory_data() # Refresh the output tab's tree view
            except Exception as e:
                 self.statusBar.showMessage(f"Error during directory scanning: {e}")
                 QMessageBox.critical(self, "Error", f"An error occurred during directory scanning:\n{e}")


    def process_selection(self):
        # ... (Keep existing process_selection method as is) ...
        # ... existing code ...
        # Create a QMessageBox instance to allow styling
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Selection Type for Processing")
        msg_box.setText("What do you want to process?\n\nYes: Select a Folder\nNo:  Select a Batch File (batch_*.txt)")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setStyleSheet("QLabel { color: black; }")
        selection_dialog = msg_box.exec_()

        if selection_dialog == QMessageBox.Yes:
            # Suggest starting directory based on tree view selection if available
            start_dir = self.current_selected_dir_path if self.current_selected_dir_path and os.path.isdir(self.current_selected_dir_path) else QDir.homePath()
            folder = QFileDialog.getExistingDirectory(self, "Select Folder to Process", start_dir)
            if folder:
                self.statusBar.showMessage(f"Processing folder: {folder}...")
                QApplication.processEvents() # Update UI
                try:
                    process_batch.process_directory(folder)
                    # Create a QMessageBox instance to allow styling
                    info_box = QMessageBox(self)
                    info_box.setIcon(QMessageBox.Information)
                    info_box.setWindowTitle("Folder Processing Complete")
                    info_box.setText(f"Finished processing directory:\n{folder}")
                    info_box.setStyleSheet("QLabel { color: black; }")
                    info_box.exec_()
                    self.statusBar.showMessage("Folder processing complete!")
                except Exception as e:
                    self.statusBar.showMessage(f"Error processing folder: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred processing the folder:\n{e}")

        elif selection_dialog == QMessageBox.No: # Explicitly check for No
            file_filter = "Batch Files (batch_*.txt);;All Files (*.*)"
            # Start in the expected output directory for batch files
            start_dir = os.path.abspath("Output/file_batches")
            if not os.path.exists(start_dir):
                 start_dir = QDir.homePath() # Fallback if dir doesn't exist

            file_path, _ = QFileDialog.getOpenFileName(self, "Select Batch File to Process", start_dir, file_filter)
            if file_path:
                self.statusBar.showMessage(f"Processing batch file: {file_path}...")
                QApplication.processEvents() # Update UI
                try:
                    process_batch.process_batch(file_path)
                     # Create a QMessageBox instance to allow styling
                    info_box = QMessageBox(self)
                    info_box.setIcon(QMessageBox.Information)
                    info_box.setWindowTitle("Batch Processing Complete")
                    info_box.setText(f"Finished processing batch file:\n{file_path}")
                    info_box.setStyleSheet("QLabel { color: black; }")
                    info_box.exec_()
                    self.statusBar.showMessage("Batch processing complete!")
                except Exception as e:
                    self.statusBar.showMessage(f"Error processing batch file: {e}")
                    QMessageBox.critical(self, "Error", f"An error occurred processing the batch file:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply a style hint for better integration if available
    # app.setStyle('Fusion')
    window = SeekerApp()
    window.show()
    sys.exit(app.exec_())
