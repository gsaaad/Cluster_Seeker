# Running Cluster Seeker
Seeker is a distributed file system analysis tool designed for large-scale directory scanning and file metadata extraction that works locally and on HPC clusters. It efficiently processes massive directory structures by leveraging SLURM job scheduling to parallelize operations across compute nodes, making it ideal for analyzing petabyte-scale file systems.


### Step 1: Assess Directory Size
```bash
# Check directory size (Linux/macOS)
du -sh /path/to/directory

# Check directory size (Windows)
dir /s "C:\path\to\directory"
```

### Step 2: Execute Based on Size

#### For directories **LESS than 200GB** - Use Local Processing
```bash
python seeker.py /path/to/folder
```

**Advantages:**
- Simple single-command execution
- No SLURM configuration required
- Immediate results
- Ideal for smaller datasets and quick analysis

#### For directories **MORE than 200GB** - Use Cluster Processing
```bash
python Cluster_Seeker.py --config config.json --folder "/path/to/folder"
```
