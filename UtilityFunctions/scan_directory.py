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

def scan_directory(directory, output_file, job_id):
    """Scan a single directory for subdirectories and write results to output file."""
    print(f"Job {job_id}: Scanning directory {directory}")
    subdirs = []
    excluded_folders = ['.', '..', '.DS_Store', '.git', '.ipynb_checkpoints', '__pycache__', 'AppData', 'node_modules', '.venv','AnaConda3','.vscode']

    directory_path = Path(convert_path_format(directory))

    try:
        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if d not in excluded_folders and not d.startswith('.')]
            for dir in dirs:
                subdirs.append(os.path.join(root, dir))
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")

    # Filter to only include leaf directories
    if subdirs:
        child_dirs = filter_child_directories(subdirs)
    else:
        child_dirs = []

    print(f"Job {job_id}: Found {len(child_dirs)} directories in {directory}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        for subdir in child_dirs:
            f.write(f"{subdir}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scan a directory for subdirectories.')
    parser.add_argument('--directory', type=str, required=True, help='Directory to scan.')
    parser.add_argument('--output_file', type=str, required=True, help='Output file for results.')
    parser.add_argument('--job_id', type=int, required=True, help='Job ID for logging.')

    args = parser.parse_args()

    scan_directory(args.directory, args.output_file, args.job_id)
