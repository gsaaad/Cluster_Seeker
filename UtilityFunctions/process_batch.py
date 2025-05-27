import os
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import argparse
import time

todays_date = time.strftime("%m-%d")

def process_directory(directory):
    # for file in directory that starts with batch_ and ends with .txt
    for file in os.listdir(directory):
        if file.startswith("batch_") and file.endswith(".txt"):
            print(f"Processing batch file: {file}")
            batch_file_path = os.path.join(directory, file)
            # run process_batch.py with the batch file as argument
            os.system(f"python process_batch.py --path \"{batch_file_path}\"")

# Enable long path support by prefixing with \\?\
def safe_path(path):
    if os.name == 'nt':
        return f"\\\\?\\{path}"


# Function to gather file information
def gather_file_info(directories):
    file_info_list = []
    for directory in directories:
        folder_path = Path(directory)
        for root, _, files in tqdm(os.walk(folder_path), desc=f"Scanning {directory}"):
            for file in files:
                try:
                    file_path = Path(root) / file
                    print("file_path: ", file_path)
                    safe_file_path = file_path
                    print(f"DEBUG: Attempting os.stat on: {repr(safe_file_path)}")
                    stats = os.stat(safe_file_path)
                    file_size = stats.st_size
                    file_size = os.path.getsize(safe_file_path)
                    created_time = os.path.getctime(safe_file_path)
                    modified_time = os.path.getmtime(safe_file_path)
                    file_extension = file_path.suffix.lower()
                    file_info_list.append([file, file_extension, file_size, created_time, modified_time, str(file_path)])
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
    return file_info_list

def process_batch(file):
    with open(file, 'r') as bf:
        directories = [line.strip() for line in bf]

    # Gather information from all directories in the batch
    all_file_info = gather_file_info(directories)
    print("We got information for ", len(all_file_info), " files.")

    # Create DataFrame
    columns = ['File Name', 'File Extension', 'File Size', 'Created Time', 'Modified Time', 'File Path']
    df = pd.DataFrame(all_file_info, columns=columns)

    # Convert times from epoch to human-readable format with date and time
    df['Created Time'] = pd.to_datetime(df['Created Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
    df['Modified Time'] = pd.to_datetime(df['Modified Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
    # output path is parent folder of the batch file with the same name but with _output.csv
    parent_folder = os.path.dirname(os.path.dirname(file))
    print("Parent folder: ", parent_folder)
    output_path = os.path.join(parent_folder, f"{os.path.basename(file).replace('.txt', '')}.csv")

    print("Saving Excel files...")
    with pd.ExcelWriter(output_path.replace('.csv', '_all_files.xlsx')) as writer:
        df.to_excel(writer, sheet_name='All Files', index=False)

    # Save extensions only to another Excel file
    with pd.ExcelWriter(output_path.replace('.csv', '_extensions.xlsx')) as writer:
        df.groupby('File Extension').apply(
            lambda x: x.to_excel(
            writer,
            sheet_name=(
                'Empty Ext' if not x.name or x.name == '.'
                else f"{x.name.strip('.')}"
            ),
            index=False
            )
        )
    print("Excel files saved.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a batch of directories.')
    parser.add_argument('--path', type=str, default="Output/file_batches", help='Path to the batch file or directory.')
    args = parser.parse_args()

    batches_path = args.path
    if not os.path.exists(batches_path):
        # use output/file_batches
        batches_path = os.path.join('Output', 'file_batches', batches_path)
        if not os.path.exists(os.path.dirname(batches_path)):
            os.makedirs(os.path.dirname(batches_path))

    if os.path.isfile(batches_path):
        process_batch(batches_path)
    elif os.path.isdir(batches_path):
        process_directory(batches_path)
    else:
        print("The provided path is neither a file nor a directory.")
