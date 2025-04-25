import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                            QMessageBox, QTabWidget, QGroupBox, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from UtilityFunctions import list_all_directories, process_batch

class SeekerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seeker")
        self.setMinimumSize(600, 400)

        # Set style sheet for modern dark theme
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
        """)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create tab widget
        tab_widget = QTabWidget()

        # Create tabs
        local_tab = self.create_local_tab()

        # Add tabs to widget
        tab_widget.addTab(local_tab, "Local Seeker")

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)

        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_local_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # List Directories Group
        list_group = QGroupBox("Directory Listing")
        list_layout = QVBoxLayout()

        list_description = QLabel("First, select directories to scan for files. This will create a list of subdirectories and batch files.")
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

        process_description = QLabel("After listing, select a folder or batch file to process. This will analyze files in the selected location.")
        process_description.setWordWrap(True)
        process_layout.addWidget(process_description)

        process_btn = QPushButton("Select Folder/File")
        process_btn.setIcon(QIcon.fromTheme("document-open"))
        process_btn.clicked.connect(self.process_selection)
        process_layout.addWidget(process_btn)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        # Add spacer at bottom
        layout.addStretch()

        tab.setLayout(layout)
        return tab


    def list_directories(self):
        output_file = "Output/subdirectories.txt"
        output_folder = "Output/file_batches"
        selected_directories = []

        # Create Output directories if they don't exist
        os.makedirs("Output", exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

        while True:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory:
                selected_directories.append(directory)
                continue_dialog = QMessageBox.question(self, "Continue",
                                                      "Do you want to select another directory?",
                                                      QMessageBox.Yes | QMessageBox.No)
                if continue_dialog == QMessageBox.No:
                    break
            else:
                break

        if selected_directories:
            print("All selected directories:", selected_directories)
            QMessageBox.information(self, "Selected Directories", "\n".join(selected_directories))
            self.status_bar.showMessage("Processing directories...")

            # Run list_all_directories on the selected directories
            list_all_directories.process_directories(selected_directories, output_file, output_folder)
            self.status_bar.showMessage("Directory listing complete!")

    def process_selection(self):
        selection_dialog = QMessageBox.question(self, "Selection Type",
                                              "Do you want to select a folder?\nYes: Folder\nNo: Batch File",
                                              QMessageBox.Yes | QMessageBox.No)

        if selection_dialog == QMessageBox.Yes:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.status_bar.showMessage(f"Processing folder: {folder}...")
                process_batch.process_directory(folder)
                QMessageBox.information(self, "Folder Processing", f"Processed directory:\n{folder}")
                self.status_bar.showMessage("Folder processing complete!")
        else:
            file_filter = "Batch Files (batch_*.txt);;All Files (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Batch File", "", file_filter)
            if file_path:
                self.status_bar.showMessage(f"Processing batch file: {file_path}...")
                process_batch.process_batch(file_path)
                QMessageBox.information(self, "Batch Processing", f"Processed batch file:\n{file_path}")
                self.status_bar.showMessage("Batch processing complete!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeekerApp()
    window.show()
    sys.exit(app.exec_())
