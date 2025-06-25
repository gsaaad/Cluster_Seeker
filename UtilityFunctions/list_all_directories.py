import os
import argparse
import platform
from pathlib import Path
from tqdm import tqdm

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

def get_excluded_folders():
    """Returns comprehensive list of folders to exclude from scanning."""

    # Basic system and hidden folders
    basic_excluded = [
        '.', '..', '.DS_Store', '.git', '.gitignore', '.gitattributes',
        '.ipynb_checkpoints', '__pycache__', '.vscode', '.idea',
        'node_modules', '.npm', '.yarn'
    ]

    # Python-specific folders
    python_excluded = [
        'site-packages', 'Lib', 'lib', 'lib64', 'Scripts', 'bin',
        '.venv', 'venv', 'env', '.env', 'virtualenv',
        '__pycache__', '.pytest_cache', '.mypy_cache',
        'build', 'dist', '*.egg-info', '.tox'
    ]

    # Development and IDE folders
    dev_excluded = [
        '.vscode', '.idea', '.eclipse', '.settings',
        '.vs', '.vscode-server', '.devcontainer',
        'CMakeFiles', 'cmake-build-debug', 'cmake-build-release'
    ]

    # Package managers and dependencies
    package_excluded = [
        'node_modules', '.npm', '.yarn', 'bower_components',
        'vendor', 'packages', 'deps'
    ]

    # Operating system specific
    os_excluded = [
        # Windows
        'AppData', 'ProgramData', '$RECYCLE.BIN', 'System Volume Information',
        'Windows', 'Program Files', 'Program Files (x86)', 'pagefile.sys',
        'hiberfil.sys', 'swapfile.sys', 'DumpStack.log.tmp',

        # macOS
        '.Spotlight-V100', '.Trashes', '.fseventsd', '.TemporaryItems',
        '.DocumentRevisions-V100', '.PKInstallSandboxManager',

        # Linux
        '/proc', '/sys', '/dev', '/run', '/tmp', '/var/cache',
        '/var/log', '/var/tmp', '.cache', '.local/share/Trash'
    ]

    # Software-specific folders
    software_excluded = [
        # Anaconda/Miniconda
        'AnaConda3', 'Anaconda3', 'miniconda3', 'Miniconda3',
        'anaconda', 'miniconda', 'envs', 'pkgs', 'conda-meta',

        # Databases
        '.sqlite', '.db', 'mysql', 'postgresql', 'mongodb',

        # Logs and temporary files
        'logs', 'log', 'temp', 'tmp', 'cache', '.cache',
        'temporary', 'staging', 'backup', 'backups',

        # Version control
        '.svn', '.hg', '.bzr', 'CVS',

        # Docker
        '.docker', 'docker-compose',

        # Cloud storage sync folders (optional - might want to scan these)
        # '.dropbox', '.onedrive', '.googledrive', '.icloud'
    ]

    # Large file/media folders that might slow down scanning (optional)
    media_excluded = [
        # Uncomment if you want to exclude these
        # 'Videos', 'Movies', 'Music', 'Photos', 'Pictures',
        # 'Downloads', 'Desktop'  # Be careful with these!
    ]

    # Combine all exclusion lists
    all_excluded = (basic_excluded + python_excluded + dev_excluded +
                   package_excluded + os_excluded + software_excluded +
                   media_excluded)

    # Remove duplicates and return
    return list(set(all_excluded))

def should_exclude_path(path, excluded_folders):
    """
    Check if a path should be excluded based on exclusion rules.

    Args:
        path (str): The path to check
        excluded_folders (list): List of folder names/patterns to exclude

    Returns:
        bool: True if the path should be excluded, False otherwise
    """
    path_obj = Path(path)

    # Check if any part of the path matches excluded folders
    for part in path_obj.parts:
        if part in excluded_folders:
            return True

    # Check for partial matches or patterns
    path_str = str(path).lower()
    for excluded in excluded_folders:
        excluded_lower = excluded.lower()

        # Exact folder name match
        if f"/{excluded_lower}/" in path_str or f"\\{excluded_lower}\\" in path_str:
            return True

        # Path ends with excluded folder
        if path_str.endswith(f"/{excluded_lower}") or path_str.endswith(f"\\{excluded_lower}"):
            return True

        # Special patterns
        if excluded_lower.startswith('*') and path_str.endswith(excluded_lower[1:]):
            return True

    return False

def estimate_directory_count(folder, excluded_folders):
    """Estimate the total number of directories for progress tracking."""
    total_dirs = 0
    try:
        for root, dirs, files in os.walk(folder):
            if should_exclude_path(root, excluded_folders):
                continue

            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d), excluded_folders)]
            total_dirs += len(dirs)

            # Stop after reasonable sample for large directories
            if total_dirs > 10000:
                return total_dirs * 2  # Rough estimate

    except Exception:
        return 1000  # Default estimate if counting fails

    return max(total_dirs, 1)  # Ensure at least 1 for progress bar

def list_subdirectories(folder, output_file):
    subdirs = []
    excluded_folders = get_excluded_folders()

    print(f"Scanning folder: {folder}")
    print(f"Excluding {len(excluded_folders)} folder types...")

    debug_exclusions = False  # Set to True for debugging

    print("Estimating directory count for progress tracking...")
    estimated_total = estimate_directory_count(folder, excluded_folders)

    if not should_exclude_path(folder, excluded_folders):

        subdirs.append(folder)
        tqdm.write(f"Included base folder: {folder}")

    with tqdm(total=estimated_total, desc="Scanning directories", unit="dirs") as pbar:
        dirs_processed = 0

        for root, dirs, files in os.walk(folder):
            if should_exclude_path(root, excluded_folders):
                if debug_exclusions:
                    print(f"EXCLUDED ROOT: {root}")
                continue

            dirs_to_remove = []
            for dir_name in dirs:
                full_dir_path = os.path.join(root, dir_name)
                if should_exclude_path(full_dir_path, excluded_folders):
                    dirs_to_remove.append(dir_name)
                    if debug_exclusions:
                        print(f"EXCLUDED DIR: {full_dir_path}")
                else:
                    if not debug_exclusions:
                        tqdm.write(f"Directory not excluded: {dir_name}")

            for dir_to_remove in dirs_to_remove:
                dirs.remove(dir_to_remove)

            for dir_name in dirs:
                subdir_path = os.path.join(root, dir_name)
                # --- Remove the is_parent check to include all directories ---
                if os.path.commonpath([subdir_path, folder]) == folder:
                    subdirs.append(subdir_path)
                    tqdm.write(f"Subdirectory found: {subdir_path}")

            dirs_processed += len(dirs)
            if dirs_processed <= estimated_total:
                pbar.update(len(dirs))
            else:
                pbar.total = dirs_processed + 100
                pbar.refresh()

    print(f"\nSkipping child directory filtering to include all directories...")
    child_dirs = subdirs  # <-- This now includes all directories, not just leaves
    seen = set()
    child_dirs = [x for x in child_dirs if not (x in seen or seen.add(x))]
    print(f"Writing {len(child_dirs)} directories to file...")
    with open(output_file, 'w') as f:
        for subdir in tqdm(child_dirs, desc="Writing directories", unit="dirs"):
            f.write(f"{subdir}\n")

    if not child_dirs:
        print("No subdirectories found.")
    else:
        print(f"Found {len(child_dirs)} directories to process.")

    return child_dirs

def split_directories(textFile, output_folder):
    print("Splitting directories into batches...")

    with open(textFile, 'r') as f:
        lines = f.readlines()

    print("Number of directories: ", len(lines))
    batch_size = 500
    batch_number = 1
    batch = []

    # Use tqdm to show progress while splitting
    for i, line in enumerate(tqdm(lines, desc="Creating batches", unit="dirs")):
        line = line.strip()
        batch.append(line)

        if (i + 1) % batch_size == 0 or i == len(lines) - 1:
            batch_file = os.path.join(output_folder, f'batch_{batch_number}.txt')
            with open(batch_file, 'w') as bf:
                for dir in batch:
                    bf.write(f"{dir}\n")

            tqdm.write(f"Created batch {batch_number} with {len(batch)} directories")
            batch_number += 1
            batch = []

    print(f"Created {batch_number - 1} batch files in {output_folder}")

def process_directories(folders):
    print("Folders to process: ", folders)

    output_folder = os.path.join(folders, 'Seeker_Output/file_batches')
    output_file = os.path.join(folders, 'Seeker_Output/subdirectories.txt')

    # Create output directories if they don't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # List subdirectories with progress tracking
    child_directories = list_subdirectories(folders, output_file)

    # Split into batches with progress tracking
    if child_directories:
        split_directories(output_file, output_folder)
    else:
        print("No directories found to split into batches.")

    return child_directories

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List all subdirectories and split them into batches.')
    parser.add_argument('--folders', nargs='+', required=False, help='List of folders to scan for subdirectories.')
    parser.add_argument('--show-excluded', action='store_true', help='Show the list of excluded folder patterns.')
    parser.add_argument('--debug', action='store_true', help='Enable debug output to see excluded directories.')
    args = parser.parse_args()

    if args.show_excluded:
        excluded = get_excluded_folders()
        print("Excluded folder patterns:")
        for folder in sorted(excluded):
            print(f"  - {folder}")
        print(f"\nTotal: {len(excluded)} exclusion patterns")
        exit(0)

    system = platform.system()
    print(f"System detected: {system}")

    if not args.folders:
        default_folders = [r'path/to/folder1', r'path/to/folder2']
        if system == "Windows":
            args.folders = default_folders
        else:  # Linux or other Unix-like
            input_folder = [convert_path_format(folder) for folder in default_folders]
            print("No folders specified. Please provide --folders argument.")
            exit(1)

    # Ensure the Output directory exists
    output_file = 'Output/subdirectories.txt'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Convert paths and process
    if args.folders:
        input_folder = [convert_path_format(folder) for folder in args.folders]
        print(f"Processing folder: {input_folder[0]}")

        # Enable debug mode if requested
        if args.debug:
            # This would require modifying list_subdirectories to accept debug parameter
            print("Debug mode enabled - excluded directories will be shown")

        process_directories(input_folder[0] if input_folder else '.')
    else:
        print("No valid folders to process.")
