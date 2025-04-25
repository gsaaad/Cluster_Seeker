# How to use SEEKER on your own computer (GPU recommended)

1.  **Step 1: Install Anaconda (if you already have it, skip)**
    a.  Go to: https://www.anaconda.com/download
    b.  Choose your Operating system [windows/mac/linux], and download the Anaconda installer.
    c.  Execute the installer you downloaded. When it asks, “Install for:,”
        i.  Choose ‘Just Me’ and press next.
    d.  Keep the installation path as default, press next.
    e.  **Important:** Check the box ‘Add Anaconda3 to my PATH environment variable’, then press Install/Next.

2.  **Step 2: Download Visual Studio Code (VSC) (if you already have it, skip)**
    a.  Go to: https://code.visualstudio.com/download
    b.  Choose your Operating system [windows/mac/linux], and download.
    c.  Execute the installer you downloaded, and follow the instructions.
    d.  Make sure to check ‘Add to PATH’ during installation.

3.  **Step 3: Open Visual Studio Code**
    a.  Use the search bar or start menu to find ‘Visual Studio Code’ and open the application.

4.  **Step 4: Open the SEEKER Workspace**
    a.  In VS Code, click the menu icon (☰) in the top left corner or use the `File` menu.
    b.  Select `File` > `Open Folder...`
    c.  Navigate to and select the SEEKER folder: `z:\migratedData\Lab\LabTools\Seeker` and click `Select Folder`.

5.  **Step 5: Open a Terminal in VS Code**
    a.  Click the menu icon (☰) or use the `Terminal` menu.
    b.  Select `Terminal` > `New Terminal`. A terminal panel will open at the bottom.

6.  **Step 6: Install SEEKER Environment**
    a.  In the VS Code terminal, type the following commands one by one, pressing Enter after each. If prompted to proceed (e.g., `[y/n]`), type `y` and press Enter. Keep track of which command you've entered, as some may take time.
    b.  Change directory to SEEKER:
        ```bash
        cd z:\migratedData\Lab\LabTools\Seeker
        ```
    c.  Create the conda environment (named `SEEKER` using Python 3.10):
        ```bash
        conda create -n SEEKER python=3.10
        ```
    d.  Activate the new environment:
        ```bash
        conda activate SEEKER
        ```
        *(You should see `(SEEKER)` at the beginning of your terminal prompt)*
    e.  Install SEEKER and its dependencies:
        ```bash
        pip install .
        ```
        *(This assumes SEEKER can be installed from the root directory using pip. Adjust if necessary based on SEEKER's setup instructions.)*

7.  **Step 7: Run SEEKER**
    a.  Ensure Visual Studio Code is open with the SEEKER folder (`z:\migratedData\Lab\LabTools\Seeker`).
    b.  Open a new terminal if you don't have one open (`Terminal` > `New Terminal`).
    c.  Change directory (if necessary):
        ```bash
        cd z:\migratedData\Lab\LabTools\Seeker
        ```
    d.  Activate the conda environment:
        ```bash
        conda activate SEEKER
        ```
    e.  *(Optional)* Open the main SEEKER script (e.g., `run_seeker.py` - **replace with the actual script name**) using the Explorer panel on the left [Shortcut: Ctrl+Shift+E].
    f.  *(Optional)* Specify any required parameters within the script or configuration file as needed by SEEKER (e.g., input data paths, model files, output directories). Refer to SEEKER's specific usage instructions.
    g.  Run the main SEEKER script (replace `run_seeker.py` with the actual script name):
        ```bash
        python run_seeker.py
        ```
    h.  Observe the terminal for progress. Output files should be generated in the location specified by SEEKER's configuration or defaults.
