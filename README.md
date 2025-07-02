# Running Cluster Seeker

Seeker is a distributed file system analysis tool designed for large-scale directory scanning and file metadata extraction that works locally and on HPC clusters. It efficiently processes massive directory structures by leveraging SLURM job scheduling to parallelize operations across compute nodes, making it ideal for analyzing petabyte-scale file systems.

## Core Features

- **Scalable Analysis:** Handles both small and extremely large directories, from local drives to HPC clusters.
- **Parallel Processing:** Utilizes SLURM for distributed job scheduling, enabling fast, efficient scanning.
- **Flexible Output:** Export results in multiple formats, including Excel, for further analysis.
- **Customizable Filtering:** Select specific file extension types to focus your analysis.
- **User-Friendly GUI:** Intuitive graphical interface for non-technical users.

## Seeker GUI

The Seeker GUI provides an easy-to-use interface for configuring and running scans. Users can:

- Select one or more file extension types (e.g., `.txt`, `.csv`, `.jpg`) to filter results.
- Initiate scans on local or cluster resources without command-line interaction.
- Export scan results directly to Excel files, making it simple to share or further analyze metadata.
- View progress and summary statistics in real time.

## Utilities

Seeker includes several utilities to streamline your workflow:

- **Directory Size Assessment:** Quickly estimate the size of directories to determine the best processing mode.
- **Metadata Extraction:** Gather detailed file information (size, timestamps, permissions, etc.).
- **Batch Processing:** Scan multiple directories or extension types in a single run.
- **Result Export:** Output results in CSV, Excel, or JSON formats for compatibility with other tools.
- **Cluster Integration:** Seamlessly submit and monitor jobs on SLURM-managed clusters.

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

### Use the Seeker_GUI to check all contents in SeekerOutput

```
python Seeker_GUI.py
```
Select a SeekerOutput folder and choose the desired extensions.

## Acknowledgements

Cluster Seeker was developed with contributions from [George Saad](https://github.com/gsaaad) and the [AER Lab](https://github.com/AER-Lab/AER-Spindle)
