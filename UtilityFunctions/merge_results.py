import os
import argparse
from tqdm import tqdm

def merge_directory_files(input_dir, output_file):
    """Merge all directory listing files into a single file."""
    all_directories = []

    # Read all files in the input directory
    for filename in os.listdir(input_dir):
        if filename.startswith('batch_') and filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r') as f:
                for line in f:
                    directory = line.strip()
                    if directory and directory not in all_directories:
                        all_directories.append(directory)

    print(f"Total unique directories found: {len(all_directories)}")

    # Write merged results to output file
    with open(output_file, 'w') as f:
        for directory in all_directories:
            f.write(f"{directory}\n")

    return all_directories

def split_into_batches(directories, batch_dir, batch_size=100):
    """Split directories into batch files."""
    print("Splitting directories into batches...")

    batch_number = 1
    batch = []

    for i, directory in enumerate(directories):
        batch.append(directory)
        if (i + 1) % batch_size == 0 or i == len(directories) - 1:
            batch_file = os.path.join(batch_dir, f'batch_{batch_number}.txt')
            with open(batch_file, 'w') as bf:
                for dir in batch:
                    bf.write(f"{dir}\n")
            batch_number += 1
            batch = []

    print(f"Created {batch_number-1} batch files in {batch_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge directory scan results and split into batches.')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing scan results.')
    parser.add_argument('--output_file', type=str, required=True, help='Output file for merged results.')
    parser.add_argument('--batch_dir', type=str, required=True, help='Directory for batch files.')
    parser.add_argument('--batch_size', type=int, default=100, help='Number of directories per batch.')

    args = parser.parse_args()

    # Create output directories
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    os.makedirs(args.batch_dir, exist_ok=True)

    # Merge results
    directories = merge_directory_files(args.input_dir, args.output_file)

    # Split into batches
    split_into_batches(directories, args.batch_dir, args.batch_size)
