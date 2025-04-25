import os
import argparse
from UtilityFunctions import list_all_directories, process_batch

def main():
    """Gets a folder path from command-line arguments and processes it."""
    parser = argparse.ArgumentParser(description="Process directories in a specified folder.")
    parser.add_argument("--folder", help="Path to the folder to process.")
    args = parser.parse_args()

    folder_path = args.folder

    # If folder path is not provided via argument, prompt the user
    if not folder_path:
        folder_path = input("Please enter the path to the folder: ")


    # Validate if the input path is an existing directory
    if not os.path.isdir(folder_path):
        print(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    try:
        print(f"Listing directories in '{folder_path}'...")
        # Assuming list_all_directories returns a list of directory paths
        list_all_directories.process_directories(folder_path)
        output_folder = os.path.join(folder_path, 'Seeker_Output/file_batches')

        for batch_file in os.listdir(output_folder):
            batch_file_path = os.path.join(output_folder, batch_file)
            if os.path.isfile(batch_file_path):
                print(f"Processing batch file: {batch_file_path}")
                process_batch.process_batch(batch_file_path)

        print("Batch processing finished.")

    except ImportError:
        print("Error: Could not import functions from UtilityFunctions.")
    except Exception as e:
        print(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()
