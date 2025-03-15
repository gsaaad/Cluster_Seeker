import os
import argparse
from pathlib import Path
from tqdm import tqdm

def is_parent(path, other_paths):
    path = Path(path)
    return any(Path(other).is_relative_to(path) for other in other_paths if other != str(path))

def filter_child_directories(directories):
    return [dir for dir in directories if not is_parent(dir, directories)]

def list_subdirectories(folders, output_file):
    subdirs = []
    excluded_folders = ['.', '..', '.DS_Store', '.git', '.ipynb_checkpoints', '__pycache__', 'AppData', 'node_modules', '.venv','AnaConda3','.vscode']
    for folder in tqdm(folders, desc="Scanning folders"):
        folder_path = Path(folder)
        print(f"Scanning folder: {folder_path}")
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in excluded_folders and not d.startswith('.')]
            for dir in dirs:
                subdirs.append(os.path.join(root, dir))

    child_dirs = filter_child_directories(subdirs)

    with open(output_file, 'w') as f:
        for subdir in child_dirs:
            f.write(f"{subdir}\n")

    if not child_dirs:
        print("No subdirectories found.")

def split_directories(textFile, output_folder):
    print("Splitting directories into batches...")
    with open(textFile, 'r') as f:
        lines = f.readlines()
        print("Number of directories: ", len(lines))
        batch_size = 100
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

def process_directories(folders, output_file, output_folder):
    list_subdirectories(folders, output_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    split_directories(output_file, output_folder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List all subdirectories and split them into batches.')
    parser.add_argument('--folders', nargs='+', required=True, help='List of folders to scan for subdirectories.')
    parser.add_argument('--output_file', type=str, default='Output/subdirectories.txt', help='Output file for subdirectories list.')
    parser.add_argument('--output_folder', type=str, default='Output/file_batches', help='Output folder for batches.')
    args = parser.parse_args()

    # Ensure the Output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    process_directories(args.folders, args.output_file, args.output_folder)
