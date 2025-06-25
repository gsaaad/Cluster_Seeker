import os
import argparse
import json
import time
import platform
import subprocess

def convert_path_format(path):
    """Convert path between Windows and Linux formats based on the current OS, and replace spaces with underscores."""
    print("Path is: ", path)
    # Replace spaces with underscores
    new_path = path.replace(' ', '_')
    if new_path != path and os.path.exists(path):
            # Only rename if the path exists and needs renaming
            try:
                os.rename(path, new_path)
                print(f"Renamed '{path}' -> '{new_path}'")
            except Exception as e:
                print(f"Failed to rename '{path}' -> '{new_path}': {e}")
                # Optionally, you could raise or handle this differently
    path = new_path
    system = platform.system()
    if system == "Windows":
        if path.startswith('/nfs/turbo'):
            return path.replace('/nfs/turbo/lsa-adae', 'Z:').replace('/', '\\')
        return path.replace('/', '\\')
    else:  # Linux or other Unix-like
        if path.startswith('Z:'):
            if '\\' not in path:
                parts = path[2:].split('migratedData')[1:]
                if parts:
                    reconstructed = '/nfs/turbo/lsa-adae/migratedData' + '/'.join(parts)
                else:
                    reconstructed = '/nfs/turbo/lsa-adae/migratedData'
                print(f"Reconstructed path: {reconstructed}")
                return reconstructed.replace('//', '/')
            path = path.replace('\\', '/')
            print("Path after replacing backslashes: ", path)
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
    script_path = os.path.join('slurm_logs', f"{job_name}.sh")

    try:
        with open(script_path, 'w') as script_file:
            script_file.write("#!/bin/bash\n")
            script_file.write(f"#SBATCH --job-name={job_name}\n")
            script_file.write(f"#SBATCH --output={log_file}\n")
            script_file.write(f"#SBATCH --error={log_file}\n")
            script_file.write(f"#SBATCH --time={config['time']}\n")
            script_file.write(f"#SBATCH --mem={config['mem']}\n")
            script_file.write(f"#SBATCH --cpus-per-task={config['cpus_per_task']}\n")

            if 'partition' in config:
                script_file.write(f"#SBATCH --partition={config['partition']}\n")
            if 'account' in config:
                script_file.write(f"#SBATCH --account={config['account']}\n")

            script_file.write("\n")

            if 'module' in config:
                if isinstance(config['module'], list):
                    for module in config['module']:
                        script_file.write(f"module load {module}\n")
                else:
                    script_file.write(f"module load {config['module']}\n")

            if 'conda_env' in config:
                script_file.write("source ~/.bashrc\n")
                script_file.write(f"conda activate {config['conda_env']}\n")

            if 'conda_lib_path' in config:
                script_file.write(f"export LD_LIBRARY_PATH={config['conda_lib_path']}:$LD_LIBRARY_PATH\n")

            if 'project_directory' in config:
                script_file.write(f"cd {config['project_directory']}\n")

            script_file.write("\n")

            converted_directory = convert_path_format(directory)
            print(f"Converted directory path: {converted_directory}")

            output_file = os.path.join(output_dir, f"subdirectories_{job_index}.txt")

            script_file.write(f"python UtilityFunctions/list_all_directories.py --folder \"{converted_directory}\"\n")

            expected_output = os.path.join(converted_directory, 'Seeker_Output', 'subdirectories.txt')
            script_file.write(f"if [ -f \"{expected_output}\" ]; then\n")
            script_file.write(f"    cp \"{expected_output}\" \"{output_file}\"\n")
            script_file.write(f"    echo \"Job {job_index} completed successfully\"\n")
            script_file.write(f"else\n")
            script_file.write(f"    echo \"Warning: Expected output file not found: {expected_output}\"\n")
            script_file.write(f"    touch \"{output_file}\"\n")
            script_file.write(f"fi\n")

        print(f"Created SLURM script: {script_path}")
        return script_path

    except Exception as e:
        print(f"Error creating SLURM script {script_path}: {e}")
        return None

def create_merge_and_process_job(config, job_ids, output_dir, batch_output_dir):
    """Create a SLURM job to merge results AND process batch files to generate Excel sheets."""

    job_name = "merge_and_process"
    log_file = os.path.join('slurm_logs', f"{job_name}.txt")
    dependency_string = f"afterok:{':'.join(job_ids)}"
    script_path = os.path.join('slurm_logs', f"{job_name}.sh")

    # convert paths to ensure compatibility
    output_dir = convert_path_format(output_dir)
    batch_output_dir = convert_path_format(batch_output_dir)

    try:
        with open(script_path, 'w') as script_file:
            script_file.write("#!/bin/bash\n")
            script_file.write(f"#SBATCH --job-name={job_name}\n")
            script_file.write(f"#SBATCH --output={log_file}\n")
            script_file.write(f"#SBATCH --error={log_file}\n")
            script_file.write(f"#SBATCH --time={config['time']}\n")
            script_file.write(f"#SBATCH --mem={config['mem']}\n")
            script_file.write(f"#SBATCH --cpus-per-task={config['cpus_per_task']}\n")
            script_file.write(f"#SBATCH --dependency={dependency_string}\n")

            if 'partition' in config:
                script_file.write(f"#SBATCH --partition={config['partition']}\n")
            if 'account' in config:
                script_file.write(f"#SBATCH --account={config['account']}\n")

            script_file.write("\n")

            if 'module' in config:
                if isinstance(config['module'], list):
                    for module in config['module']:
                        script_file.write(f"module load {module}\n")
                else:
                    script_file.write(f"module load {config['module']}\n")

            if 'conda_env' in config:
                script_file.write("source ~/.bashrc\n")
                script_file.write(f"conda activate {config['conda_env']}\n")

            if 'conda_lib_path' in config:
                script_file.write(f"export LD_LIBRARY_PATH={config['conda_lib_path']}:$LD_LIBRARY_PATH\n")

            if 'project_directory' in config:
                script_file.write(f"cd {config['project_directory']}\n")

            script_file.write("\n")

            # Step 1: Merge all individual result files
            merged_file = os.path.join(batch_output_dir, "all_subdirectories.txt")
            script_file.write(f"echo \"Step 1: Merging scan results...\"\n")
            script_file.write(f"cat {output_dir}/subdirectories_*.txt > \"{merged_file}\"\n")
            script_file.write(f"echo \"Merged $(wc -l < \"{merged_file}\") total directories\"\n")

            # Step 2: Split into batches
            script_file.write(f"echo \"Step 2: Creating batch files...\"\n")
            script_file.write(f"python -c \"\n")
            script_file.write(f"import sys; sys.path.append('.')\n")
            script_file.write(f"from UtilityFunctions.list_all_directories import split_directories\n")
            script_file.write(f"split_directories('{merged_file}', '{batch_output_dir}')\n")
            script_file.write(f"\"\n")
            script_file.write(f"echo \"Batch files created in {batch_output_dir}\"\n")

            # Step 3: Process each batch file to generate Excel sheets in output_dir
            script_file.write(f"echo \"Step 3: Processing batch files to generate Excel sheets...\"\n")
            script_file.write(f"batch_count=0\n")
            script_file.write(f"success_count=0\n")
            script_file.write(f"for batch_file in {batch_output_dir}/batch_*.txt; do\n")
            script_file.write(f"    if [ -f \"$batch_file\" ]; then\n")
            script_file.write(f"        echo \"Processing batch file: $batch_file\"\n")
            script_file.write(f"        batch_count=$((batch_count + 1))\n")

            # Change to output_dir so Excel files are created there
            script_file.write(f"        cd {output_dir}\n")
            script_file.write(f"        python {config.get('project_directory', '.')}/UtilityFunctions/process_batch.py --path \"$batch_file\"\n")
            script_file.write(f"        if [ $? -eq 0 ]; then\n")
            script_file.write(f"            success_count=$((success_count + 1))\n")
            script_file.write(f"            echo \"SUCCESS: Generated Excel files for $batch_file in {output_dir}\"\n")
            script_file.write(f"        else\n")
            script_file.write(f"            echo \"ERROR: Failed to process $batch_file\"\n")
            script_file.write(f"        fi\n")
            # Return to project directory
            script_file.write(f"        cd {config.get('project_directory', '.')}\n")
            script_file.write(f"    fi\n")
            script_file.write(f"done\n")

            # Step 4: Report results (look for Excel files in output_dir, not batch_output_dir)
            script_file.write(f"echo \"\\nProcessing Summary:\"\n")
            script_file.write(f"echo \"- Processed $success_count out of $batch_count batch files successfully\"\n")
            script_file.write(f"echo \"- Excel files generated in: {output_dir}\"\n")
            script_file.write(f"echo \"- Batch files stored in: {batch_output_dir}\"\n")
            script_file.write(f"echo \"\\nGenerated Excel files:\"\n")
            script_file.write(f"ls -la {output_dir}/*.xlsx 2>/dev/null || echo 'No Excel files found in {output_dir} - check for errors above'\n")

        print(f"Created merge and process SLURM script: {script_path}")
        return script_path

    except Exception as e:
        print(f"Error creating merge and process SLURM script: {e}")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch SLURM jobs to list subdirectories and generate Excel files.')
    parser.add_argument('--config', type=str, required=True, help='Path to SLURM configuration JSON file.')
    parser.add_argument('--folder', nargs='+', required=True, help='Folder to scan for subdirectories.')

    args = parser.parse_args()

    # Load configuration with error handling
    try:
        with open(args.config, 'r') as config_file:
            config = json.load(config_file)
        print(f"Loaded configuration from: {args.config}")
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        exit(1)

    # Validate required configuration fields
    required_fields = ['time', 'mem', 'cpus_per_task']
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        print(f"Error: Missing required configuration fields: {missing_fields}")
        exit(1)

    if not args.folder:
        print("Error: --folder argument is required")
        exit(1)

# Use the provided folder directly as the base for our output
    base_folder = args.folder[0]  # Use the first provided folder as base
    print(f"Base folder provided: {base_folder}")

    # Create output directories in the provided folder location
    args.output_dir = os.path.join(base_folder, 'Seeker_Output')  # Main output folder
    args.batch_dir = os.path.join(args.output_dir, 'file_batches')  # Batch files folder


    # Convert and validate paths
    folders_to_scan = []
    print("Folders to scan: ", args.folder)

    # Convert all input folders
    for folder in args.folder:
        converted = convert_path_format(folder)
        print(f"Converted '{folder}' -> '{converted}'")
        folders_to_scan.append(converted)

    # Convert base_folder for consistency
    converted_base_folder = convert_path_format(base_folder)

    # Ensure base folder is included
    if converted_base_folder not in folders_to_scan:
        folders_to_scan.append(converted_base_folder)

    # Create output directories using the converted base folder
    args.output_dir = os.path.join(converted_base_folder, 'Seeker_Output')
    args.batch_dir = os.path.join(args.output_dir, 'file_batches')

    # Validate directories
    valid_folders = []
    for folder in folders_to_scan:
        if os.path.isdir(folder):
            valid_folders.append(folder)
            print(f"✓ Valid directory: {folder}")
        else:
            print(f"✗ Invalid directory: {folder}")

    if not valid_folders:
        print("Error: No valid directories found.")
        exit(1)

    folders_to_scan = valid_folders
    # add base folder to the list if not already included
    if base_folder not in folders_to_scan:
        folders_to_scan.append(base_folder)

    print("Final list of directories to scan:", folders_to_scan)

    # Submit scanning jobs
    job_ids = []
    print(f"\nLaunching {len(folders_to_scan)} SLURM jobs for directory scanning...")

    for i, directory in enumerate(folders_to_scan):
        print(f"\nCreating job {i+1}/{len(folders_to_scan)} for: {directory}")

        script_path = create_slurm_job_for_directory(directory, config, i, args.output_dir)

        if script_path is None:
            continue

        try:
            result = subprocess.run(['sbatch', script_path],
                                  capture_output=True, text=True, check=True)
            output = result.stdout.strip()

            if "Submitted batch job" in output:
                job_id = output.split()[-1]
                int(job_id)  # Validate it's a number
                job_ids.append(job_id)
                print(f"✓ Submitted job {job_id}")
            else:
                print(f"✗ Unexpected SLURM output: {output}")

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to submit job: {e}")
            continue
        except (IndexError, ValueError) as e:
            print(f"✗ Failed to parse job ID: {e}")
            continue

        time.sleep(0.1)

    if not job_ids:
        print("Error: No jobs were successfully submitted.")
        exit(1)

    print(f"\n✓ Successfully submitted {len(job_ids)} scanning jobs: {job_ids}")

    # Submit merge and processing job
    print("\nCreating merge and Excel generation job...")
    merge_script = create_merge_and_process_job(config, job_ids, args.output_dir, args.batch_dir)

    if merge_script is None:
        print("Failed to create merge job script.")
        exit(1)

    try:
        merge_result = subprocess.run(['sbatch', merge_script],
                                    capture_output=True, text=True, check=True)
        merge_output = merge_result.stdout.strip()

        if "Submitted batch job" in merge_output:
            merge_job_id = merge_output.split()[-1]
            print(f"✓ Submitted merge and processing job {merge_job_id}")
        else:
            print(f"✗ Failed to submit merge job: {merge_output}")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error submitting merge job: {e}")

    print(f"\n" + "="*60)
    print(f"COMPLETE WORKFLOW SUMMARY")
    print(f"="*60)
    print(f"📁 Scanning jobs: {len(job_ids)} submitted")
    print(f"🔗 Job IDs: {job_ids}")
    print(f"📊 Processing job: Will merge results and generate Excel files")
    print(f"📂 Excel files will be in: {args.batch_dir}")
    print(f"📋 Expected files: batch_1_all_files.xlsx, batch_1_extensions.xlsx, etc.")
    print(f"🔍 Monitor with: squeue -u $USER")
    print(f"📄 Check logs in: slurm_logs/")
    print(f"="*60)
