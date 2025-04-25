import os
import argparse
import platform
from pathlib import Path

def is_parent(path, other_paths):
    path = Path(path)
    return any(Path(other).is_relative_to(path) for other in other_paths if other != str(path))

def filter_child_directories(directories):
    return [dir for dir in directories if not is_parent(dir, directories)]

def convert_path_format(path):
    """Convert path between Windows and Linux formats based on the current OS."""
    system = platform.system()

    if system == "Windows":
        # If on Windows and path looks like a Linux path starting with /nfs/turbo
        if path.startswith('/nfs/turbo'):
            return path.replace('/nfs/turbo/lsa-adae', 'Z:').replace('/', '\\')
        return path.replace('/', '\\')
    else:  # Linux or other Unix-like
        # If on Linux and path looks like a Windows path starting with Z:
        if path.startswith('Z:'):
            return path.replace('Z:', '/nfs/turbo/lsa-adae').replace('\\', '/')
        return path.replace('\\', '/')

def list_subdirectories(folder, output_file):
    subdirs = []
    excluded_folders = ['.', '..', '.DS_Store', '.git', '.ipynb_checkpoints', '__pycache__', 'AppData', 'node_modules', '.venv','AnaConda3','.vscode']
    for root, dirs, files in os.walk(folder):
        if root not in excluded_folders:
            for dir in dirs:
                if dir not in excluded_folders:
                    print("Directory not excluded: ", dir)
                    subdir_path = os.path.join(root, dir)
                    # check again that the dir and parent folder are not in the excluded folders
                    if not any(excluded in subdir_path for excluded in excluded_folders):
                        # check if the subdir is a child of any other directory
                        if not is_parent(subdir_path, subdirs):
                            # check if the subdir is a child of the parent folder
                            if os.path.commonpath([subdir_path, folder]) == folder:
                                subdirs.append(subdir_path)
                                print("Subdirectory found: ", subdir_path)

    child_dirs = filter_child_directories(subdirs)

    with open(output_file, 'w') as f:
        for subdir in child_dirs:
            f.write(f"{subdir}\n")

    if not child_dirs:
        print("No subdirectories found.")
    return child_dirs

def split_directories(textFile, output_folder):
    print("Splitting directories into batches...")
    with open(textFile, 'r') as f:
        lines = f.readlines()
        print("Number of directories: ", len(lines))
        batch_size = 200
        batch_number = 1
        batch = []

        for i, line in enumerate(lines):
            line = line.strip()
            batch.append(line)
            if (i + 1) % batch_size == 0 or i == len(lines) - 1:
                batch_file = os.path.join(output_folder, f'batch_{batch_number}.txt')
                with open(batch_file, 'w') as bf:
                    for dir in batch:
                        bf.write(f"{dir}\n")
                batch_number += 1
                batch = []

def process_directories(folders):
    parent_folder = os.path.dirname(folders[0])
    output_folder = os.path.join(parent_folder, 'Seeker_Output/file_batches')
    output_file = os.path.join(parent_folder, 'Seeker_Output/subdirectories.txt')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    child_directories = list_subdirectories(folders, output_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    split_directories(output_file, output_folder)
    return child_directories

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List all subdirectories and split them into batches.')
    parser.add_argument('--folders', nargs='+', required=False, help='List of folders to scan for subdirectories.')
    args = parser.parse_args()


    system = platform.system()
    if not args.folders:
        default_folders = [r'path/to/folder1', r'path/to/folder2']
        if system == "Windows":
            args.folders = default_folders
        else:  # Linux or other Unix-like
            args.folders = [convert_path_format(folder) for folder in default_folders]

    # Ensure the Output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    process_directories(args.folders)
