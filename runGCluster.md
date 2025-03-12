# Running GCluster Scripts

## Step 1: List All Directories
Before running any other scripts, start by executing the `list_all_directories` script.
Add the folders you want to search for, on line 64
This script will generate an array of target directories that you want to change or investigate further. Run the script and observe the output to ensure that the correct directories are being listed.
## Step 2: Split Directories into Batches

After listing all the directories, the next step is to split them into batches by executing `split_directories.py`. Ideally, each batch should contain 50 directories per computer. This step is important to distribute the workload evenly across multiple machines. Implement the necessary code to split the directories into batches.

## Step 3: Launch Slurm Job
Once the directories are split into batches, you can proceed to launch the Slurm job.
`python launch_slurm_jobs.py --config config.json --batches_dir file_batches`
The Slurm job will process each batch separately and generate a CSV file for each job. Make sure to configure the Slurm job parameters according to your requirements.

## Step 3A: Check Slurm Job
<!-- Check slurm job -->

`squeue -p standard | grep 'geosaad'`

## Step 4: Run Combined Find Dup
After all the Slurm jobs have completed and generated their respective CSV files, you can run the combined find dup script. This script will combine all the CSV files and identify any duplicates among them. Execute the combined find dup script to complete the process.

