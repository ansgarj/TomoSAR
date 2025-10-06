# README
This repository contains the `tomosar` python module, which also provides a selection of [Core CLI Tools](#Core%20CLI%20Tools) that can be run directly from the terminal. It can be installed into your  `Python` environment via `pip`.  You can either **clone** the repository and install it as a development module (`-e`), this is the route suggested below, or you can install it directly from the repository:
```sh
pip install git+https://github.com/ansgarj/TomoSAR.git
```

If you clone the repository you will have local access to the code for experimentation and your own development (you can later create your own _branch_ and `git push` that branch and make _pull requests_ to merge your _branch_ to the `main` branch, see [[#collaboration|below]]), and you can `git pull` any updates and see the changes immediately reflected in your environment.

If you choose to install directly from the online repository. You have access to it as is, but to update it you have to run:
```sh
pip install --force-reinstall --no-cache-dir git+https://github.com/yourusername/TomoSAR.git
```
You also do not have local access to the code.

Included below is some basic GitHub usage, but there is also plenty of documentation online (e.g. pulling specific versions or branches).

## Installation
**NOTE**: It is recommended to use a Python virtual environment when installing the module. This allows you to have separate Python environments for different projects, avoiding any potential conflicts, and is also _required_ by some Linux distributions in order to avoid potential conflicts with _system Python_. It also makes it _easier to reproduce your setup_ on another computer should you wish to. Below is described an example setup _with a virtual environment_.

You can place your virtual environment anywhere, but I have placed it in the associated project folder:
```sh
git clone https://github.com/ansgarj/TomoSAR.git
cd TomoSAR
python3 -m venv .venv
source .venv/bin/activate
python install -r requirements.txt
pip install -e ./TomoSAR
```

In the above example the Python virtual environment is created inside a `.venv` folder inside the `TomoSar` project directory. I find this helpful to contain the project in one directory, but if you plan to `git push` changes you must also create a `.gitignore` file inside the `TomoSar` directory containing e.g.:
```sh
# Python virtual environment
.venv/

# Byte-compiled / cache files
__pycache__/
```
and any other files or subdirectories you do not want to push to GitHub. 

**NOTE**:I have a simple shell function that I include into my `.bashrc` file to activate virtual environments by alias e.g.:
```sh
# Activate virtual environments by alias
activate() {
    local alias="$1"
    local project_path=""

    case "$alias" in 
        sar)
            project_path="$HOME/TomoSar/"
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

### Post-Install
The `tomosar` module relies on some 3rd party software for GNSS processing. It is recommended to make sure you have everything set up before starting to use the toolbox, even though it is not _strictly_ necessary. To facilitate this there is CLI tool that you can run:
```sh
tomotest binaries
```
This will check if there are any binaries in your `PATH` with the correct names, but not actually test if it is the correct binaries, and provide helpful information if not (including source html links where applicable). The required binaries are:
1. `convbin` from `rtklib`
2. `rnx2rtkp` from `rtklib`
3. `crx2rnx` from GSI Japan
4. `gfzrnx` from GFZ Potsdam
5. `glab` from ESA
6. `unimoco` from Radaz

**NOTE**: some of the binaries will have different names, e.g. `CRX2RNX` or `gLAB_linux` when downloaded, but the name provided above and by `tomotest binaries` are the names the `tomosar` module uses and the binaries should either be _renamed_ and moved into the `PATH` _or_ you can create a _symlink_ with the correct name in the `PATH`. 
## Usage
The `tomosar` module is a work-in-progress to provide a one-stop toolbox for our tomographic SAR needs. Once installed it can be imported into Python by running `import tomosar`, or you can select submodules or objects as usual  in Python. Currently, the only available documentation is the one present in the code, _but I plan to add separate documentation later._

The **CLI tools** are intended to provide a toolbox for the most common or predicted needs, the idea being that unless you are working on your own project with something not integrated into the CLI tools, you can use the module directly from the terminal by running a command without having to enter into Python and importing the module.  All tools can be called with `-h` or `--help` for some basic syntax. 

### Core CLI Tools
These are the core tools for a drone processing workflow:
1. `tomotest`: used for various tests
	1. `tomotest binaries`: looks in `PATH` for the necessary binaries
	2. `tomotest gnss`: performs a minimal test of GNSS processing
	3. `tomotest ppp`: tests base station PPP performance against ground truth as given in a `mocoref.moco` file
2. `tomoprocess`: used for all things processing
3. `tomoload`: used for viewing tomograms, statistics, e.t.c
...
4. `process-dir`: **NOT IMPLEMENTED** directly generates a processing directory from a [data directory](#data-directories). It will identify what files are present, and if necessary subsititute for a missing `mocoref.moco` file by running `station-ppp` on the GNSS base station observation file, or subsitute for missing GNSS base station files by downloading rinex files from _Swepos_. Then it will copy all necessary files into a processing directory located in `../../Processed/{name}_{today}` where `{name}` is the name of the data directory and `{today}` is the date when the processing directory was generated (for tracking different processings). The generated directory will have the correct file structure for **Radaz** functions. Finally `process-dir` initiates `preprocess` in the processing directory.
5. `analyze-spirals`: **IN PROCESS** analyzes and models the spiral tracks (calls `trackfinder` if necessary) to provide information on optimal processing parameters for `tomoprocess`. 
6. `tomoprocess`: **NOT IMPLEMENTED** uses `tomoslice` and `tomoforge` to process all slices for a tomogram, and then combines them into a [tomogram directory](#tomogram-directories). If processing parameters are not specified: `tomoprocess` will itself call `analyze-spirals` to identify what it considers optimal parameters.

### Utility CLI tools
These tools are utilities that may be helpful for a modified work flow or troubleshooting:
1. `station-ppp`: runs PPP processing on a GNSS base station directory to find its position, updates the rinex header with the correct position and generates a `mocoref.moco` file (**mocoref generation not fully implemented**). In theory this can be _more precise_ than using Emlid with NTRIP but because we don't have exact antenna calibration data for the GNSS we have used (CHCI83) it is limited by manual identification of correct antenna phase offset centers, and **this is done by comparison with Emlid NTRIP measurements**. Thus they should be approximately equivalent.
2. `fetch-swepos`: downloads and merges the necessary rinex data from the nearest station in the  _Swepos_ network, for any given drone `gnss_logger_dat-[...].bin` file. These file have the correct exact position in the RINEX header, but will be more distant from the flight (longer _baseline_ which can introduce other errors: in testing it is roughly equivalent to using our GNSS with Emlid NTRIP measurement of the position). **Note**: in the process it will use `convbin` to convert the UBX .bin file to RINEX files if this is not done already.
3. `preprocess`: **NOT IMPLEMENTED** subsititutes for `gdl -q -e proz,/heli` by correctly identifying the GNSS rinex files and uses `trackfinder` to identify the correct track timestamps for _spiral flights_.
4. `trackfinder`: Correctly identifies all tested flight timestamps and generates the `radar[...].inf` file for spiral flight processing. Can be used to generate the correct timestamps for linear flights by `trackfinder -l` or more generally `trackfinder -l X`. 
5.  `tomoslice`: **NOT IMPLEMENTED** initiates a _backprojection_ loop to generate all slices for the specified tomogram.
6. `tomoforge`: scans paths for slice files and intelligently combines them into [tomogram directories](#tomogram-directories). 
7. `sliceinfo`: scans a directory for slice files and provides information on them.
### Other CLI tools
These tools are generated because of development needs, and are not stable. They may change significantly or be removed in future updates (please let me know if you want any to be made stable):
1. `compare-pos`: compares the output `.pos` file solutions for RTKP processing using two different base station files (includes RTKP processing if needed);
2. `inspect-out`: inspects the results of `tomoprocess ppp`;
3. `rnx-info`: provides timestamps and approximate location for a RINEX observation file;
4. `read-imu`: experimentally reads a `imu_logger_dat-[...].bin` file and generates a `.csv` file from it. 
### Data Directories

### Tomogram Directories
## Collaboration
