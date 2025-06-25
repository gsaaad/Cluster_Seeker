import os
import shutil
import argparse

def copy_and_rename_filtered_csv(src_dir, dest_dir, keyword, replacement):
    """
    Recursively searches for *_filtered.csv files in src_dir, copies them to dest_dir,
    and renames the files by replacing 'keyword' with 'replacement' in the filename.
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('_filtered_labeled.mp4'):
                src_file = os.path.join(root, file)
                # Rename the file by replacing keyword in the filename
                new_filename = file.replace(keyword, replacement)
                dest_file = os.path.join(dest_dir, new_filename)
                shutil.move(src_file, dest_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copy and rename filtered CSV files.')
    parser.add_argument('src_dir', type=str, help='Source directory to search for *_filtered.csv files')
    parser.add_argument('dest_dir', type=str, help='Destination directory to copy the files to')
    parser.add_argument('keyword', type=str, help='Keyword to be replaced in the filenames')
    parser.add_argument('replacement', type=str, help='Replacement string for the keyword')

    args = parser.parse_args()

    copy_and_rename_filtered_csv(args.src_dir, args.dest_dir, args.keyword, args.replacement)
