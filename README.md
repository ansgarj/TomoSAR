# README
This repository contains the `tomosar` python module which is **under development**, which also provides a selection of [CLI Tools](#core-cli-tools) that can be run directly from the terminal. It can be installed into your  `Python` environment via `pip`.  You can either **clone** the repository and install it as a development module (`-e`), this is the route suggested below, or you can install it directly from the repository:
```sh
pip install git+https://github.com/ansgarj/TomoSAR.git
```

If you clone the repository you will have local access to the code for experimentation and your own development (you can later create your own _branch_ and `git push` that branch and make _pull requests_ to merge your _branch_ to the `main` branch, see [Collaboration](#collaboration)), and you can `git pull` any updates and see the changes immediately reflected in your environment.

If you choose to install directly from the online repository. You have access to it as is, but to update it you have to run:
```sh
pip install --force-reinstall --no-cache-dir git+https://github.com/yourusername/TomoSAR.git
```
You also will not be able to modify or develop the code yourself.

Included below is some basic GitHub usage, but there is also plenty of documentation online (e.g. pulling specific versions or branches).

## Installation
**NOTE**: It is recommended to use a Python virtual environment when installing the module. This allows you to have separate Python environments for different projects, avoiding any potential conflicts, and is also _required_ by some Linux distributions in order to avoid potential conflicts with _system Python_. It also makes it _easier to reproduce your setup_ on another computer should you wish to. Below is described an example setup _with a virtual environment_.

You can place your virtual environment anywhere, but I have placed it in the associated project folder:
```sh
git clone https://github.com/ansgarj/TomoSAR.git
cd TomoSAR
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
tomosar setup
```

**NOTE**: running `tomosar setup` is not strictly required, but will install a Git _hook_ for you, check if all required binaries are present and help you if not, and pre-warm the \_\_pycache\_\_ (see more [below](#cli-tools))

In the above example the Python virtual environment is created inside a `.venv` folder inside the `TomoSar` project directory. I find this helpful to contain the project in one directory. **Note**: do _not_ use another name for the virtual environment if placed inside the project directory, but _if you do_ then you must add this folder to the `.gitignore` file, e.g.:
```sh
...

# Python virtual environment
.venv/
my-venv/ 

# Byte-compiled / cache files
...
```
Also add any other files or subdirectories should not be pushed to GitHub that you keep inside the project directory that I have not added (if any).

**NOTE**:I have a simple shell function that I include into my `.bashrc` file to activate virtual environments by alias e.g.:
```sh
# Activate virtual environments by alias
activate() {
    local alias="$1"
    local project_path=""

    case "$alias" in 
        sar)
            project_path="$HOME/TomoSAR/"
            ;;
        *)
            echo "Unknown project alias: $alias"
            return 1
            ;;
    esac
    source "$project_path/.venv/bin/activate"
}
```
That way I can activate the virtual environment by running e.g. `activate sar` from any folder (say, where I have the radar data). 

### Required Binaries
The `tomosar` module relies on some 3rd party software for GNSS processing. It is recommended to make sure you have everything set up before starting to use the toolbox, even though it is not _strictly_ necessary. If you run `tomosar setup` as suggested above, this is already done. Otherwise you can run
```sh
tomosar dependencies
```
to perform the check independently. This will check if there are any binaries in your `PATH` with the correct names, but not actually test if it is the correct binaries, and provide helpful information if not (including source html links where applicable). The required binaries are:
1. `convbin` from `rtklib`
2. `rnx2rtkp` from `rtklib`
3. `crx2rnx` from GSI Japan
4. `gfzrnx` from GFZ Potsdam
5. `glab` from ESA
6. `unimoco` from Radaz

**NOTE**: some of the binaries will have different names, e.g. `CRX2RNX` or `gLAB_linux` when downloaded, but the name provided above and by `tomotest binaries` are the names the `tomosar` module uses and the binaries should either be _renamed_ and moved into the `PATH` _or_ you can create a _symlink_ with the correct name in the `PATH`. 

**NOTE**: I use the [demo5](https://github.com/rinex20/RTKLIB-demo5) version of `rtklib`, and this is the one `tomotest binaries` will suggest installing if it finds no `convbin` or `rnx2rtkp` binary, **but** it _should_ run on standard `rtklib` as well.

## Usage
The `tomosar` _module_ is a work-in-progress to provide a one-stop toolbox for our tomographic SAR needs. Once installed it can be imported into Python by running `import tomosar`, or you can select submodules or objects as usual  in Python. Currently, the only available documentation is the one present in the code, _but I plan to add separate documentation later._

The [CLI tools](#cli-tools) are intended to provide a toolbox for the most common or predicted needs, the idea being that unless you are working on your own project with something not integrated into the CLI tools, you can use the module directly from the terminal by running a command without having to enter into Python and importing the module.  All tools can be called with `--help` for some basic syntax. 

### Environment Variables
The following environment variables are used by the `tomosar` module to locate files that are kept _only locally_ for memory reasons: `TOMOMASKS` (used to locate `.shp` masks), `TOMODEMS` (used to locate `.tif` files that provide DEM:s) and `TOMOCANOPIES` (used to locate `.tif` files that provide DSM:s used to identify **canopy** ). If not set, `tomosar` will default to using only the user provided folder (see documentation). It is recommended to set the variables in order to avoid needing to track them manually. Note that
- `TOMOMASKS` _or a user passed substitute_ is **never** required;
- `TOMODEMS` _or a user passed substitute_ is **required** only when processing slices with a ground reference;
- `TOMOCANOPIES` _or a user passed substitute_ is **required** only when processing slices with a canopy reference.

### CLI Tools
These are the CLI tools provided by the `tomosar` module:
1. `tomosar`:  version, help, setup, planning and various Python entry points:
	1. `tomosar version`: prints the current version.
	2. `tomosar help`: prints this README with some formatting
	3. `tomosar setup`: installs a Git _hook_ that performs `setup` whenever a successful merge occurs (i.e. on future `git pull` runs, **note**: this is skipped if a `post-merge` Git hook already exists, so you _can_ modify and use your own hooks), then continues setup by checking if the `pyproject.toml` file changed in the last merge (if no merge found it falls back to last commit) and updates the installation if it did, checks if all required binaries are in the `PATH` (in case more were added) and prints helpful information if not, and finally it pre-warms the \_\_pycache\_\_ by compiling the module with all sub-modules and tools.
	4. `tomosar dependencies`: performs the `PATH` check for required binaries independently of `setup`.
	5. `tomosar warmup`: pre-warms the \_\_pycache\_\_.
	6. `tomosar optimize`: **NOT IMPLEMENTED** plans a flight for optimizing _nominal_ SAR parameters according to given restraints.
	7. `tomosar plan`: **NOT IMPLEMENTED** interactively models a _planned flight_ to allow validation of ideal SAR parameters across different tomograms (**Note**: this does not take into account flight instabilities that can occur during the actual flight).
	8. `tomosar sliceinfo`: scans a directory for slice files and collects them into a `SliceInfo` object, and then opens an interactive Python console with the `SliceInfo` object stored under `slices`. 
	9. `tomosar load`: loads a single [Tomogram Directory](#tomogram-directories) or multiple [Tomogram Directories](#tomogram-directories) into a `TomoScenes` object, and then opens an interactive Python console with the `TomoScenes` object stored under `tomos`. 
2. `tomotest`: used for various tests
	1. `tomotest gnss`: **NOT IMPLEMENTED** tests GNSS processing capabilities, ensuring that your binaries work as intended and are compatible with the module.
	2. `tomotest ppp`: **NOT IMPLEMENTED** tests base station PPP performance against ground truth as given in a `mocoref.moco` file.
3. `tomoprocess`: used for all things processing
	1. `tomoprocess init`: **NOT IMPLEMENTED** directly generates a processing directory from a [Data Directory](#data-directories). It will identify what files are present, if necessary generate a `mocoref.moco` file from a CSV file using `mocoref` or if necessary subsititute for a missing mocoref data by running `ppp` on the GNSS base station observation file, or subsitute for missing GNSS base station files by downloading rinex files from _Swepos_ using `swepos`. Then it will copy all necessary files into a processing directory located in `../../Processing/{name}_{today}` where `{name}` is the name of the data directory and `{today}` is the date when the processing directory was generated (for tracking different processings). The generated directory will have the correct file structure for **Radaz** functions. Finally `process-dir` initiates `preprocess` in the processing directory.
	2. `tomoprocess mocoref`: **NOT IMPLEMENTED** generates a correctly formatted `mocoref.moco` file from a CSV file,  reading the columns named `Longitude`, `Latitude`, `Ellipsoidal height` and `Antenna height` (default column names from _Emlid Reach_) for mocoref data. If multiple lines are present in the CSV files it will by default read the first line (modify by `--line X`). Antenna height can be specified manually, overriding CSV data by `--antenna X`. 
	3. `tomoprocess ppp`: runs PPP processing on a GNSS base station directory to find its position, updates the rinex header with the correct position and generates a `mocoref.moco` file (**mocoref generation not fully implemented**). In theory this can be _more precise_ than using Emlid with NTRIP but because we don't have exact antenna calibration data for the GNSS we have used (CHCI83) it is limited by manual identification of correct antenna phase offset centers, and **this is done by comparison with Emlid NTRIP measurements**. Thus they should be approximately equivalent.
	4. `tomoprocess swepos`: downloads and merges the necessary rinex data from the nearest station in the  _Swepos_ network, for any given drone `gnss_logger_dat-[...].bin` file. These file have the correct exact position in the RINEX header, but will be more distant from the flight (longer _baseline_ which can introduce other errors: in testing it is roughly equivalent to using our GNSS with Emlid NTRIP measurement of the position). **Note**: in the process it will use `convbin` to convert the UBX .bin file to RINEX files if this is not done already.
	5. `tomoprocess pre`: **NOT IMPLEMENTED** subsititutes for `gdl -q -e proz,/heli` by correctly identifying the GNSS rinex files and uses `trackfinder` to identify the correct track timestamps for _spiral flights_.
	6. `tomoprocess trackfinder`: correctly identifies all tested flight timestamps and generates the `radar[...].inf` file for spiral flight processing. Can be used to generate the correct timestamps for linear flights by `trackfinder -l` or more generally `trackfinder -l X`. 
	7. `tomoprocess analysis`: **NOT IMPLEMENTED** analyzes the spiral flights and models them. Used to verify _idealized flight_ vs. _planned flight_, and to inspect _realized flight_ parameters, including anisotropies from flight instabilities. Can provide optimal processing parameters for `tomo`/`slice`. 
	8. `tomoprocess tomo`: **NOT IMPLEMENTED** chains `slice` and `forge` to generate a [Tomogram Directory](#tomogram-directories), or content for one. 
	9. `tomoprocess slice`: **NOT IMPLEMENTED** initiates a _backprojection_ loop to generate all slices for the specified tomogram.
	10. `tomoprocess forge:` scans paths for slice files and intelligently combines them into [Tomogram Directories](#tomogram-directories)
4. `tomoview`: used for viewing tomograms, statistics, e.t.c
	1. ...

### Data Directories
As a _data directory_ functions anything containing at least the done data. There are no specific requirements on the _internal_ structure. However, if `tomoprocess dir` is to be used to generate _processing directories_, a _data directory_ should be placed inside a containing folder next to a `Processing` folder, e.g.:
```
.../
 |-- Campaigns/
 |     |-- 20250617_krycklan/
 |     |-- 20250827_0100_krycklan/
 |     |-- ...
 |- Processing/
 |     |-- 20250617_krycklan_20251001/
 |     |-- 20250617_krycklan_20251006/
 |     |-- 20250827_0100_krycklan_20251006/
 |     |-- ...
 |- Tomograms/
 |     |-- [...].tomo
```

### Tomogram Directories
A _Tomogram Directory_ is an output directory ending with `.tomo` generated by `tomoprocess forge` or `tomoprocess tomo`, which contains _all relevant files_ and serves as an output repository for _processed data_. It contains an _internal structure_ that must be maintained, and any files contained in there can be accessed normally for 3rd party software or file sharing et.c. It is thus a **unified** output format for storing processed data, making collaboration easier.

However, the **main advantage** of the `.tomo` directories is that they can be loaded directly by `tomoload` for viewing the tomogram, plotting statistics or other analysis tools (**under implementation**). 

```
yyyy-mm-dd-HH-MM-SS-XX-tag.tomo/
|-- flight_info.json
|-- moco_cut.csv
|-- phh
|    |-- processing_parameters.json
|    |-- raw_tomogram.tif
|    |-- multilooked_tomogram.tif
|    |-- filtered_tomogram.tif
|    |-- raw_statistics.csv
|    |-- multilooked_statistics.csv
|    |-- filtered_statistics.csv
|    |-- masked_statistics/
|    |       |-- <mask1>_raw_statistics.csv
|    |       |-- <mask1>_multilooked_statistics.csv
|    |       |-- <mask1>_filtered_statistics.csv
|    |       |-- <mask2>_raw_statistics.csv
|    |       |-- ...
|    |-- cached_masks/
|    |       |-- <mask1>.npy
|    |       |-- <mask1>.json
|    |       |-- <mask2>.npy
|    |       |-- ...
|    |-- .slices/
|    |       |-- dbr_[...]C.tif
|    |       |-- ...
|-- cvv
|    |-- ...
|-- lhh
|    |-- ...
|-- ...
```
## Collaboration
If you want to modify the module or work on features to add, always **create your own branch**:
1. `git checkout -b feature/my-branch` (here _feature_ is a descriptive flag to signal a feature addition, but could be anything or nothing and _my-branch_ is a name for this particular branch)
2. Edit files, add content, et.c.
3. `git add .` inside the local repository
4. `git commit -m "Write a description here"`
5. `git push origin feature/my-branch`
6. You can then go to [GitHub](https://github.com/ansgarj/TomoSAR) and make a **pull request** for me to integrate it into the main branch

**NOTE**: to push changes you must set up your identity:
```sh
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```
Then set up authentication:
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens.
2. Click **"Generate new token"** (classic or fine-grained).
3. Select scopes like `repo` and `workflow` (for private repos).
4. Copy the token and save it securely.
5. When Git asks for your password during `git push`, **paste the token instead**.

**NOTE**: you can also change to SSH authentication (more advanced)
1.  Generate an SSH key (if you don't have one):
```sh
ssh-keygen -t ed25519 -C "your.email@example.com"
```
2. Add your SSH key to the SSH agent (assuming you used default name):
```sh
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```
3. Add the **public** key to GitHub:
```sh
cat ~/.ssh/id_ed25519.pub
```
4. Copy the output and past into GitHub → Settings → SSH and GPG keys.
5. Change your remote URL to SSH:
```sh
git remote set-url origin git@github.com:ansgarj/TomoSAR.git
```

## License
This project is licensed under the BSD 3-Clause License – see the LICENSE file for details.