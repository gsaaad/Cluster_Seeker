import tkinter as tk
from tkinter import messagebox
import os
import list_all_directories

def list_directories():
    directories = [d for d in os.listdir('.') if os.path.isdir(d)]
    messagebox.showinfo("Directories", "\n".join(directories))
    

def process_batch():
    # Placeholder for the actual batch processing function
    messagebox.showinfo("Process Batch", "Batch processing started...")

def launch_slurm_job():
    # Placeholder for the actual SLURM job launching function
    messagebox.showinfo("Launch SLURM Job", "SLURM job launched...")

# Create the main window
root = tk.Tk()
root.title("Cluster Seeker")

# Create buttons
btn_list_directories = tk.Button(root, text="List Directories", command=list_directories)
btn_list_directories.pack(pady=10)

btn_process_batch = tk.Button(root, text="Process Batch", command=process_batch)
btn_process_batch.pack(pady=10)

btn_launch_slurm = tk.Button(root, text="Launch SLURM Job", command=launch_slurm_job)
btn_launch_slurm.pack(pady=10)

# Run the application
root.mainloop()
