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

# split_directories
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

if __name__ == '__main__':
    output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output')
    output_file = 'subdirectories.txt'
    output = os.path.join(output_folder, output_file)

    parser = argparse.ArgumentParser(description='List all subdirectories.')
    parser.add_argument('--output_file', type=str, default=output, help='Output file for subdirectories.')
    args = parser.parse_args()
    folders = [r'Z:\migratedData\Lab\Social_Sleep', r'Z:\migratedData\Lab\Sotelo_2023', r'Z:\migratedData\Lab\Other 2 chamber experiments']
        # output folder is where current script is located + 'output'

    list_subdirectories(folders, args.output_file)
    output_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output/file_batches')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    split_directories(args.output_file, output_folder)
