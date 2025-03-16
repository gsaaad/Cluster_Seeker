import os
import argparse
import json
import tempfile
import time
import platform

def convert_path_format(path):
    """Convert path between Windows and Linux formats based on the current OS."""
    print("Path is: ", path)
    system = platform.system()
    print("System is: ", system)
    if system == "Windows":
        # If on Windows and given a Linux path (e.g., /nfs/turbo/lsa-adae/...), convert to Z:\ format
        if path.startswith('/nfs/turbo'):
            return path.replace('/nfs/turbo/lsa-adae', 'Z:').replace('/', '\\')
        return path.replace('/', '\\')
    else:  # Linux or other Unix-like
        # If given a Windows path starting with Z:, convert to Linux format
        if path.startswith('Z:'):
            # Handle the case where backslashes have been stripped
            if '\\' not in path:
                # This is a Windows path with stripped backslashes, add them back
                parts = path[2:].split('migratedData')[1:]
                if parts:
                    reconstructed = '/nfs/turbo/lsa-adae/migratedData' + '/'.join(parts)
                else:
                    reconstructed = '/nfs/turbo/lsa-adae/migratedData'
                print(f"Reconstructed path: {reconstructed}")
                return reconstructed.replace('//', '/')

            # Standard conversion for intact Windows paths
            # First, normalize backslashes to forward slashes
            path = path.replace('\\', '/')
            print("Path after replacing backslashes: ", path)
            # Then replace Z: with the Linux mount point, ensuring proper slash
            if path.startswith('Z:/'):
                return path.replace('Z:/', '/nfs/turbo/lsa-adae/')
            else:
                return path.replace('Z:', '/nfs/turbo/lsa-adae/')
        return path.replace('\\', '/')

def create_slurm_job_for_directory(directory, config, job_index, output_dir):
    """Create a SLURM job script to process a single directory."""

    if not os.path.exists('slurm_logs'):
        os.makedirs('slurm_logs')

    job_name = f"dir_scan_{job_index}"
    log_file = os.path.join('slurm_logs', f"{job_name}.txt")

    SBATCH_STRING = f"""#!/bin/sh
#SBATCH --account={config['account']}
#SBATCH --partition={config['partition']}
#SBATCH --job-name={job_name}
#SBATCH --output={log_file}
#SBATCH --ntasks-per-node={config['ntasks_per_node']}
#SBATCH --cpus-per-task={config['cpus_per_task']}
#SBATCH --mail-user={config['mail-user']}
#SBATCH --time={config['time']}
#SBATCH --mem={config['mem']}

source ~/.bashrc
conda activate {config['conda_env']}

export LD_LIBRARY_PATH={config['conda_lib_path']}:$LD_LIBRARY_PATH

cd {config['project_directory']}

# Run directory scanner on single directory
python scan_directory.py --directory "{directory}" --output_file "{output_dir}/batch_{job_index}.txt" --job_id {job_index}
"""

    dirpath = tempfile.mkdtemp()
    script_path = os.path.join(dirpath, f"dir_scan_{job_index}.sh")
    with open(script_path, "w") as tmpfile:
        tmpfile.write(SBATCH_STRING)

    return script_path

def create_merge_job(config, job_ids, output_dir, batch_output_dir):
    """Create a SLURM job to merge results after all scanning jobs complete."""

    job_name = "merge_scan_results"
    log_file = os.path.join('slurm_logs', f"{job_name}.txt")

    # Create job dependency string for all scan jobs
    # Format: --dependency=afterok:jobid1:jobid2:...
    dependency_string = f"afterok:{':'.join(job_ids)}"

    SBATCH_STRING = f"""#!/bin/sh
#SBATCH --account={config['account']}
#SBATCH --partition={config['partition']}
#SBATCH --job-name={job_name}
#SBATCH --output={log_file}
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --mem=8G
#SBATCH --dependency={dependency_string}

source ~/.bashrc
conda activate {config['conda_env']}

export LD_LIBRARY_PATH={config['conda_lib_path']}:$LD_LIBRARY_PATH

cd {config['project_directory']}

# Merge results and create batches
python merge_results.py --input_dir "{output_dir}" --output_file "Output/subdirectories.txt" --batch_dir "{batch_output_dir}"
"""

    dirpath = tempfile.mkdtemp()
    script_path = os.path.join(dirpath, "merge_job.sh")
    with open(script_path, "w") as tmpfile:
        tmpfile.write(SBATCH_STRING)

    return script_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch SLURM jobs to list subdirectories in parallel.')
    parser.add_argument('--config', type=str, required=True, help='Path to SLURM configuration JSON file.')
    parser.add_argument('--folders', nargs='+', required=False, help='List of folders to scan for subdirectories.')
    parser.add_argument('--output_dir', type=str, default='Output/scan_results', help='Directory to store scan results.')
    parser.add_argument('--batch_dir', type=str, default='Output/file_batches', help='Directory to store batched results.')

    args = parser.parse_args()

    # Load configuration
    with open(args.config, 'r') as config_file:
        config = json.load(config_file)

    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.batch_dir, exist_ok=True)
    os.makedirs('slurm_logs', exist_ok=True)

    # Default folders if not provided
    if not args.folders:
        print("No folders provided.. Exiting.")
        exit(1)

    # Convert paths if needed
    folders_to_scan = []
    print("Folders to scan: ", args.folders)
    print("Converting paths...")
    for folder in args.folders:
        print("Folder: ", folder)
        converted = convert_path_format(folder)
        print("Converted folder path: ", converted)
        folders_to_scan.append(converted)

    print("Paths converted.")
    print("folders_to_scan: ", folders_to_scan)

    # Check if folder is a valid directory
    valid_folders = []
    for folder in folders_to_scan:
        if os.path.isdir(folder):
            valid_folders.append(folder)
        else:
            print(f"Folder is not a valid directory. {folder}")

    if not valid_folders:
        print("Error: No valid directories found.")
        exit(1)

    folders_to_scan = valid_folders
    print("Valid folders to scan: ", folders_to_scan)

    # Submit a separate job for each directory
    job_ids = []
    job_scripts = []

    print(f"Launching {len(folders_to_scan)} SLURM jobs for directory scanning...")

    for i, directory in enumerate(folders_to_scan):
        script_path = create_slurm_job_for_directory(directory, config, i, args.output_dir)
        job_scripts.append(script_path)

        # Submit the job
        result = os.popen(f"sbatch {script_path}").read().strip()

        try:
            job_id = result.split()[-1]
            # Validate that job_id is a number
            int(job_id)  # This will raise ValueError if job_id is not a number
            job_ids.append(job_id)
            print(f"Submitted job {i} with ID {job_id} for directory: {directory}")
        except (IndexError, ValueError):
            print(f"Warning: Failed to submit job for directory: {directory}")
            print(f"SLURM output: {result}")
            continue

        time.sleep(0.1)

    if not job_ids:
        print("No jobs were successfully submitted. Exiting.")
        exit(1)

    # Create merge job that depends on all scan jobs
    merge_script = create_merge_job(config, job_ids, args.output_dir, args.batch_dir)

    # Submit merge job with dependencies
    merge_cmd = f"sbatch {merge_script}"
    merge_result = os.popen(merge_cmd).read().strip()

    try:
        merge_job_id = merge_result.split()[-1]
        print(f"Submitted merge job with ID {merge_job_id}")
    except IndexError:
        print(f"Failed to submit merge job. SLURM output: {merge_result}")

    print(f"All jobs launched. Results will be merged once all scan jobs complete.")
