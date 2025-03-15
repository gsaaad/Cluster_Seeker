import os
import tempfile
import time
import json
import argparse
from tqdm import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SLURM job launcher for searching files and directories.')
    parser.add_argument('--config', type=str, required=True, help='Path to SLURM configuration JSON file.')
    parser.add_argument('--batches_dir', type=str, default='batches', help='Path to batches directory.')

    args = parser.parse_args()

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)

    batch_directory = args.batches_dir
    target_last_folder = os.path.basename(os.path.normpath(batch_directory))
    print(f"Launching SLURM job for batch {target_last_folder}...")

    if not os.path.exists('slurm_logs'):
        os.makedirs('slurm_logs')
    SBATCH_STRING = f"""#!/bin/sh
    #SBATCH --account={config['account']}
    #SBATCH --partition={config['partition']}
    #SBATCH --job-name=searching_{batch_directory}
    #SBATCH --output={os.path.join(config['project_directory'],'slurm_logs')}searching_{target_last_folder}.txt
    #SBATCH --ntasks-per-node={config['ntasks_per_node']}
    #SBATCH --cpus-per-task={config['cpus_per_task']}
    #SBATCH --time={config['time']}
    #SBATCH --mem={config['mem']}

    source ~/.bashrc
    conda activate {config['conda_env']}

    export LD_LIBRARY_PATH={config['conda_lib_path']}:$LD_LIBRARY_PATH

    cd {config['project_directory']}

    python process_batch.py "{os.path.join(args.batches_dir, batch_directory)}"
    """

    dirpath = tempfile.mkdtemp()
    script_path = os.path.join(dirpath, "scr.sh")
    with open(script_path, "w") as tmpfile:
        tmpfile.write(SBATCH_STRING)

    for _ in tqdm(range(1), desc="Submitting SLURM job"):
        os.system(f"sbatch {script_path}")
        time.sleep(0.01)

    print(f"Launched from {script_path}")
