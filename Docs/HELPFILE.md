# General CLI help
## `tomosar`
The `tomosar` CLI command is used for a large number of _utility_ functions:
1. `tomosar version` prints the current version.
2. `tomosar settings` prints the current settings
3. `tomosar verbose` triggers verbose mode. If verbose all module commands that run 3rd party binaries will print the exact command they are running. 
4. `tomosar add` adds files or folders to file lists in settings
5. `tomosar remove` removes files or folders from file lists in settings
6. `tomosar set` sets values for other settings
7. `tomosar clear` clears a set value for some setting
8. `tomosar default` restores default settings
9. `tomosar help` prints this HELPFILE with some formatting
10. `tomosar setup` installs Git _hooks_ that performs `setup` whenever a successful merge occurs (i.e. on future `git pull` calls) and before `git push` (**note**: this is skipped if the corresponding Git hooks already exist, so you _can_ modify and use your own hooks), then updates the installation, checks if all required binaries are in the `PATH` (in case more were added) and prints helpful information if not, and finally it pre-warms the \_\_pycache\_\_ by compiling the module with all sub-modules and tools.
11. `tomosar dependencies` performs the `PATH` check for required binaries independently of `setup`.
12. `tomosar warmup` pre-warms the \_\_pycache\_\_.
13. `tomosar optimize` \[**NOT IMPLEMENTED**\] plans a flight for optimizing _nominal_ SAR parameters according to given restraints.
14. `tomosar plan` \[**NOT IMPLEMENTED**\] interactively models a _planned flight_ to allow validation of ideal SAR parameters across different tomograms (**Note**: this does not take into account flight instabilities that can occur during the actual flight).
15. `tomosar sliceinfo` scans a directory for slice files and collects them into a `SliceInfo` object, and then opens an interactive Python console with the `SliceInfo` object stored under `slices`. 
16. `tomosar load` loads a single _Tomogram Directory_ or multiple _Tomogram Directories_ into a `TomoScenes` object, and then opens an interactive Python console with the `TomoScenes` object stored under `tomos`.

## `tomotest`
The `tomotest` CLI command is used for various performance tests. Currently only GNSS related ones are planned.
1. `tomotest gnss` \[**NOT IMPLEMENTED**\] tests GNSS processing capabilities, ensuring that your binaries work as intended and are compatible with the module.
2. `tomotest ppp` \[**NOT IMPLEMENTED**\] tests base station PPP performance against ground truth as given in a `mocoref.moco` file.

## `tomoprocess`
The `tomoprocess` CLI command is used for all things processing
1. `tomoprocess data` \[**NOT IMPLEMENTED**\] fetches the **most recent** _drone data_ and generates a _Data Directory_ inside the folder pointed to by the `DATA_DIRS` setting (**default**: `$HOME/Radar/Data`)
2. `tomoprocess init` \[**NOT IMPLEMENTED**\] directly generates a processing directory from a _Data Directory_. It will identify what files are present, if necessary generate a `mocoref.moco` file from a CSV file using `mocoref` or if necessary subsititute for a missing mocoref data by running `ppp` on the GNSS base station observation file, or subsitute for missing GNSS base station files by downloading rinex files from _Swepos_ using `swepos`. Then it will copy all necessary files into a processing directory located inside the folder pointed to by the `PROCESSING_DIRS` setting (**default**: `$HOME/Radar/Processing`). The generated directory will have the correct file structure for **Radaz** functions. Finally `tomprocess init` initiates `preprocess` in the processing directory.
3. `tomoprocess mocoref` \[**NOT IMPLEMENTED**\] generates a correctly formatted `mocoref.moco` file from a CSV file,  reading the columns named `Longitude`, `Latitude`, `Ellipsoidal height` and `Antenna height` (default column names from _Emlid Reach_, can be changed with `tomosar set MOCOREF_LATITUDE`, `MOCOREF_LONGITUDE`, `MOCOREF_HEIGHT` and `MOCOREF_ANTENNA`) for mocoref data. If multiple lines are present in the CSV files it will by default read the first line (modify by `--line X`). Antenna height can be specified manually, overriding CSV data by `--antenna X`. 
4. `tomoprocess ppp` runs PPP processing on a GNSS base station directory to find its position, updates the rinex header with the correct position and generates a `mocoref.moco` file (**mocoref generation not fully implemented**). In theory this can be _more precise_ than using Emlid with NTRIP but because we don't have exact antenna calibration data for the GNSS we have used (CHCI83) it is limited by manual identification of correct antenna phase offset centers, and **this is done by comparison with Emlid NTRIP measurements**. Thus they should be approximately equivalent.
5. `tomoprocess swepos` downloads and merges the necessary rinex data from the nearest station in the  _Swepos_ network, for any given drone `gnss_logger_dat-[...].bin` file. These file have the correct exact position in the RINEX header, but will be more distant from the flight (longer _baseline_ which can introduce other errors: in testing it is roughly equivalent to using our GNSS with Emlid NTRIP measurement of the position). **Note**: in the process it will use `convbin` to convert the UBX .bin file to RINEX files if this is not done already.
6. `tomoprocess pre` \[**NOT IMPLEMENTED**\] subsititutes for `gdl -q -e proz,/heli` by correctly identifying the GNSS rinex files and uses `trackfinder` to identify the correct track timestamps for _spiral flights_.
7. `tomoprocess trackfinder` correctly identifies all tested flight timestamps and generates the `radar[...].inf` file for spiral flight processing. Can be used to generate the correct timestamps for linear flights by `trackfinder -l` or more generally `trackfinder -l X`. 
8. `tomoprocess analysis` \[**NOT IMPLEMENTED**\] analyzes the spiral flights and models them. Used to verify _idealized flight_ vs. _planned flight_, and to inspect _realized flight_ parameters, including anisotropies from flight instabilities. Can provide optimal processing parameters for `tomo`/`slice`. 
9. `tomoprocess tomo` \[**NOT IMPLEMENTED**\] chains `slice` and `forge` to generate a _Tomogram Directory_, or content for one. 
10. `tomoprocess slice` \[**NOT IMPLEMENTED**\] initiates a _backprojection_ loop to generate all slices for the specified tomogram.
11. `tomoprocess forge:` scans paths for slice files and intelligently combines them into _Tomogram Directory_.

## `tomoview`
The `tomoview` CLI command is used for viewing tomograms, statistics, e.t.c \[**NOT IMPLEMENTED**\]
