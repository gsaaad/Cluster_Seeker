import os
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import argparse
import time
import platform

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
    for entry in directories:
        entry_path = Path(entry)
        if entry_path.is_file():
            # Process single file
            try:
                stats = os.stat(entry_path)
                file_size = stats.st_size
                if platform.system() == "Windows":
                    created_time = stats.st_mtime
                    modified_time = stats.st_ctime
                    accessed_time = stats.st_atime
                    file_info_list.append([
                        entry_path.name,
                        entry_path.suffix.lower(),
                        file_size,
                        created_time,
                        modified_time,
                        accessed_time,
                        str(entry_path)
                    ])
                else:
                    modified_time = stats.st_mtime
                    change_time = stats.st_ctime
                    accessed_time = stats.st_atime
                    file_info_list.append([
                        entry_path.name,
                        entry_path.suffix.lower(),
                        file_size,
                        modified_time,
                        change_time,
                        accessed_time,
                        str(entry_path)
                    ])
            except Exception as e:
                print(f"Error processing file {entry_path}: {e}")
        elif entry_path.is_dir():
            # Process all files in directory (as before)
            for root, _, files in tqdm(os.walk(entry_path), desc=f"Scanning {entry}"):
                for file in files:
                    try:
                        file_path = Path(root) / file
                        stats = os.stat(file_path)
                        file_size = stats.st_size
                        if platform.system() == "Windows":
                            created_time = stats.st_mtime
                            modified_time = stats.st_ctime
                            accessed_time = stats.st_atime
                            file_info_list.append([
                                file,
                                file_path.suffix.lower(),
                                file_size,
                                created_time,
                                modified_time,
                                accessed_time,
                                str(file_path)
                            ])
                        else:
                            modified_time = stats.st_mtime
                            change_time = stats.st_ctime
                            accessed_time = stats.st_atime
                            file_info_list.append([
                                file,
                                file_path.suffix.lower(),
                                file_size,
                                modified_time,
                                change_time,
                                accessed_time,
                                str(file_path)
                            ])
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
    return file_info_list
def process_batch(file):
    with open(file, 'r') as bf:
        directories = [line.strip() for line in bf]

    # Gather information from all directories in the batch
    all_file_info = gather_file_info(directories)
    print("We got information for ", len(all_file_info), " files.")

    # Create DataFrame with platform-appropriate columns
    if platform.system() == "Windows":
        columns = ['File Name', 'File Extension', 'File Size', 'Created Time', 'Modified Time', 'Accessed Time', 'File Path']
    else:
        columns = ['File Name', 'File Extension', 'File Size', 'Modified Time', 'Change Time', 'Accessed Time', 'File Path']

    df = pd.DataFrame(all_file_info, columns=columns)

    # Convert times from epoch to human-readable format
    if platform.system() == "Windows":
        df['Created Time'] = pd.to_datetime(df['Created Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Modified Time'] = pd.to_datetime(df['Modified Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Accessed Time'] = pd.to_datetime(df['Accessed Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        df['Modified Time'] = pd.to_datetime(df['Modified Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Change Time'] = pd.to_datetime(df['Change Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        df['Accessed Time'] = pd.to_datetime(df['Accessed Time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')

    # Debug: Print first few rows to verify times make sense
    print("Sample data (first 3 rows):")
    print(df.head(3).to_string())

    # Validate time logic (Modified should not be later than Created on Windows)
    if platform.system() == "Windows":
        invalid_times = df[pd.to_datetime(df['Modified Time']) > pd.to_datetime(df['Created Time'])]
        if not invalid_times.empty:
            print(f"Warning: Found {len(invalid_times)} files where Modified Time > Created Time")
            print("This might indicate timestamp issues. First few examples:")
            print(invalid_times[['File Name', 'Created Time', 'Modified Time']].head())

    # output path is parent folder of the batch file with the same name but with _output.csv
    parent_folder = os.path.dirname(os.path.dirname(file))
    print("Parent folder: ", parent_folder)
    output_path = os.path.join(parent_folder, f"{os.path.basename(file).replace('.txt', '')}.csv")

    print("Saving Excel files...")
    with pd.ExcelWriter(output_path.replace('.csv', '_all_files.xlsx'), engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Files', index=False)

    # Save extensions only to another Excel file
    print("Creating extensions analysis...")
    try:
        with pd.ExcelWriter(output_path.replace('.csv', '_extensions.xlsx'), engine='openpyxl') as writer:
            # Group by extension and create sheets
            extension_groups = df.groupby('File Extension')

            for ext_name, group in extension_groups:
                # Clean sheet name (Excel has restrictions)
                if not ext_name or ext_name == '.' or ext_name == '':
                    sheet_name = 'No Extension'
                else:
                    # Remove the dot and limit length
                    sheet_name = ext_name.strip('.').replace('/', '_').replace('\\', '_')[:31]
                    if not sheet_name:
                        sheet_name = 'Unknown'

                print(f"Creating sheet for extension: {ext_name} -> {sheet_name}")
                group.to_excel(writer, sheet_name=sheet_name, index=False)

    except Exception as e:
        print(f"Error creating extensions file: {e}")
        # Fallback: save as single sheet
        with pd.ExcelWriter(output_path.replace('.csv', '_extensions_simple.xlsx'), engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Extensions', index=False)

    print("Excel files saved.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a batch of directories.')
    parser.add_argument('--path', type=str, help='Path to the batch file or directory.')
    args = parser.parse_args()

    batches_path = args.path

    if os.path.isfile(batches_path):
        process_batch(batches_path)
    elif os.path.isdir(batches_path):
        process_directory(batches_path)
    else:
        print("The provided path is neither a file nor a directory.")
