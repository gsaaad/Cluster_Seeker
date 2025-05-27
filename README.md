# Running Cluster Seeker

## Step 1: List All Directories

Before running any other scripts, start by executing the `list_all_directories` script.
Add the folders you want to search for, on line 64
or call the function: with the following parameters
python .\list_all_directories.py --folders "path/to/folder1" "path/to/folder2"

This script will generate an array of target sub-directories that you want to investigate

## Step 2: Launch Slurm Job

Once the directories are split into batches, you can proceed to launch the Slurm job.
`python launch_slurm_jobs.py --config config.json --batches_dir file_batches`
The Slurm job will process each batch separately and generate a CSV file for each job. Make sure to configure the Slurm job parameters according to your requirements.

## Step 2A: Check Slurm Job

<!-- Check slurm job -->

`squeue -p standard | grep 'UMICHUSERNAME`

## Step 3: Run Combined Find Dup

After all the Slurm jobs have completed and generated their respective CSV files, you can run the combined find dup script. This script will combine all the CSV files and identify any duplicates among them. Execute the combined find dup script to complete the process.
