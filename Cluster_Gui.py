import tkinter as tk
from tkinter import messagebox
import os
import list_all_directories
from tkinter import filedialog
import process_batch
def list_directories():
    output_file = "Output/subdirectories.txt"
    output_folder = "Output/file_batches"
    selected_directories = []
    while True:
        directory = filedialog.askdirectory(mustexist=True, title="Select Directory")
        if directory:
            selected_directories.append(directory)
            if not messagebox.askyesno("Continue", "Do you want to select another directory?"):
                break
        else:
            break
    if selected_directories:
        print("All selected directories:", selected_directories)
        messagebox.showinfo("Selected Directories", "\n".join(selected_directories))
        # Run list_all_directories on the selected directories
        list_all_directories.process_directories(selected_directories, output_file, output_folder)
def process_selection():
    if messagebox.askyesno("Selection Type", "Do you want to select a folder?\nYes: Folder\nNo: Batch File"):
        folder = filedialog.askdirectory(mustexist=True, title="Select Folder")
        if folder:
            process_batch.process_directory(folder)
            messagebox.showinfo("Folder Processing", f"Processed directory:\n{folder}")
    else:
        file_path = filedialog.askopenfilename(
            title="Select Batch File",
            filetypes=[("Batch Files", "batch_*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            process_batch.process_batch(file_path)
            messagebox.showinfo("Batch Processing", f"Processed batch file:\n{file_path}")

def launch_slurm_job():
    # Placeholder for the actual SLURM job launching function
    messagebox.showinfo("Launch SLURM Job", "SLURM job launched...")

# Create the main window
root = tk.Tk()
root.title("Cluster Seeker")

# Create buttons
# add title "Local Cluster Seeker"
title = tk.Label(root, text="Local Seeker", font=("Helvetica", 16))
btn_list_directories = tk.Button(root, text="List Directories", command=list_directories)
btn_list_directories.pack(pady=10)

btn_select = tk.Button(root, text="Select Folder/File", command=process_selection)
btn_select.pack(pady=10)

Slurm_Title = tk.Label(root, text="SLURM Cluster Seeker", font=("Helvetica", 16))



# Run the application
root.mainloop()
