import os
import shutil

def prepare_slurm_ready_folder(input_folder):
    # Create the slurm-ready folder
    slurm_ready_folder = os.path.join(input_folder, 'slurm-ready')
    os.makedirs(slurm_ready_folder, exist_ok=True)

    # Iterate over all .txt files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_folder, filename)

            # Read the content of the file
            with open(file_path, 'r') as file:
                content = file.read()

            # Replace Z:\ with /nfs/turbo/lsa-adae/ and backslashes with forward slashes
            content = content.replace('Z:\\', '/nfs/turbo/lsa-adae/').replace('\\', '/')

            # Write the modified content to a new file in the slurm-ready folder
            new_file_path = os.path.join(slurm_ready_folder, filename)
            with open(new_file_path, 'w') as new_file:
                new_file.write(content)

# Example usage
folder = r'Z:\migratedData\Lab\George\Python\George-Scripts\output\file_batches'
prepare_slurm_ready_folder(folder)
