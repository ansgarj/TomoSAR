import click
from pathlib import Path
import json
from getpass import getpass
import re

from ..config import Settings, save_default
from ..utils import warn

def read_three_numbers(prompt) -> list:
    user_input = input(f"{prompt} (enter 3 numbers): ")

    # Regex to match floats including scientific notation
    pattern = r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?'

    # Find all matches
    matches = re.findall(pattern, user_input)

    # Convert to float
    float_list = [float(m) for m in matches]

    # Validate count
    if len(float_list) != 3:
        print("Please enter exactly 3 numbers.")
        float_list = read_three_numbers()
    return float_list

def verify_atx(file_path: str|Path):
    """
    Checks if the .atx file has a valid header with:
    - Line 1: exactly 5 leading spaces before version, 12 spaces between version and system flag,
              valid system flag (G, R, E, C, J, S, M), and ends with 'ANTEX VERSION / SYST'
    - Line 2: starts with 'A' as PCV TYPE, 60 spaces before 'PCV TYPE / REFANT',
              REFANT field must be empty, and ends with 'PCV TYPE / REFANT'
    Returns True if all conditions are met, otherwise False.
    """
    valid_system_flags = {'G', 'R', 'E', 'C', 'J', 'S', 'M'}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line1 = f.readline()
            line2 = f.readline()

            # Line 1 checks
            if not line1.endswith("ANTEX VERSION / SYST\n"):
                return False
            if not line1.startswith("     "):  # 5 leading spaces
                return False
            version_str = line1[5:10].strip()
            inter_space = line1[10:22]
            if inter_space != " " * 12:
                return False
            system_flag = line1[22].strip()
            try:
                version = float(version_str)
            except ValueError:
                return False
            if version < 1.4 or system_flag not in valid_system_flags:
                return False

            # Line 2 checks
            if not line2.endswith("PCV TYPE / REFANT\n"):
                return False
            pcv_type = line2[0].strip()
            refant_field = line2[1:60]
            if pcv_type != 'A' or refant_field != " " * 59:
                return False

            return True
    except Exception as e:
        print(f"Error reading file: {e}")
        return False


@click.command()
def default() -> None:
    """Restore default settings"""
    save_default()
    print("TomoSAR settings restored to default.")

@click.command()
def settings() -> None:
    """Display settings"""
    Settings().print()

@click.command()
def verbose() -> None:
    """Toggle verbose mode"""
    st = Settings()
    if st.VERBOSE:
        st.VERBOSE = False
        print("VERBOSE toggled OFF")
    else:
        st.VERBOSE = True
        print("VERBOSE toggled ON")
    st.save()

@click.group()
def set() -> None:
    """Set value for settings"""
    pass

@set.command()
@click.argument("value", required=False)
def MOCOREF_LONGITUDE(value) -> None:
    """Update MOCOREF_LONGITUDE"""
    st = Settings()
    print(f"Current value: {st.MOCOREF_LONGITUDE}")
    if value is None:
        value = input("Enter new value: ")
    st.MOCOREF_LONGITUDE = value
    st.save()

@set.command()
@click.argument("value", required=False)
def MOCOREF_LATITUDE(value) -> None:
    """Update MOCOREF_LATITUDE"""
    st = Settings()
    print(f"Current value: {st.MOCOREF_LATITUDE}")
    if value is None:
        value = input("Enter new value: ")
    st.MOCOREF_LATITUDE = value
    st.save()

@set.command()
@click.argument("value", required=False)
def MOCOREF_HEIGHT(value) -> None:
    """Update MOCOREF_HEIGHT"""
    st = Settings()
    print(f"Current value: {st.MOCOREF_HEIGHT}")
    if value is None:
        value = input("Enter new value: ")
    st.MOCOREF_HEIGHT = value
    st.save()

@set.command()
@click.argument("value", required=False)
def MOCOREF_ANTENNA(value) -> None:
    """Update MOCOREF_ANTEANNA (antenna height)"""
    st = Settings()
    print(f"Current value: {st.MOCOREF_ANTENNA}")
    if value is None:
        value = input("Enter new value: ")
    st.MOCOREF_ANTENNA = value
    st.save()

@set.command()
@click.argument("value", required=False)
def DATA_DIRS(value) -> None:
    """Update DATA_DIRS (path where data directories are generated)"""
    st = Settings()
    print(f"Current value: {st.DATA_DIRS}")
    if value is None:
        value = input("Enter new value: ")
    st.DATA_DIRS = value
    st.save()

@set.command()
@click.argument("value", required=False)
def PROCESSING_DIRS(value) -> None:
    """Update PROCESSING_DIRS (path where processing directories are generated)"""
    st = Settings()
    print(f"Current value: {st.PROCESSING_DIRS}")
    if value is None:
        value = input("Enter new value: ")
    st.PROCESSING_DIRS = value
    st.save()

@set.command()
@click.argument("value", required=False)
def TOMO_DIRS(value) -> None:
    """Update TOMO_DIRS (path where tomogram directories are generated)"""
    st = Settings()
    print(f"Current value: {st.TOMO_DIRS}")
    if value is None:
        value = input("Enter new value: ")
    st.TOMO_DIRS = value
    st.save()

@set.command()
@click.argument("path", required=False)
def RTKP_CONFIG(path) -> None:
    """Update RTKP config path"""
    st = Settings()
    print(f"Current value: {st.RTKP_CONFIG}")
    if path is None:
        path = Path(input("Enter new value: "))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File {path} not found.")
    st.RTKP_CONFIG = path
    st.save()

@set.command()
@click.argument("username", required=False)
def SWEPOS_USERNAME(username) -> None:
    """Update SWEPOS USERNAME"""
    st = Settings()
    print(f"Current username: {st.SWEPOS_USERNAME}")
    if username is None:
        username = input("Enter username: ")
    st.SWEPOS_USERNAME = username
    st.save()

@set.command()
@click.argument("password", required=False)
def SWEPOS_PASSWORD(password) -> None:
    """Update SWEPOS PASSWORD"""
    st = Settings()
    if password is None:
        password = getpass("Enter password (note: this will be saved in settings.json UNENCRYPTED): ")
    st.SWEPOS_PASSWORD = password
    st.save()

@set.command()
def DEFAULT_POC() -> None:
    """Update default POC (phase offset center) for receiver antennas"""
    st = Settings()
    print(f"Current value:")
    poc = json.dumps(st.DEFAULT_POC, indent=4)
    poc = "\n".join("    " + line for line in poc.splitlines())
    print(poc)
    value = {
        1: read_three_numbers("Frequency 1"),
        2: read_three_numbers("Frequency 2"),
        3: read_three_numbers("Frequency 3"),
        4: read_three_numbers("Frequency 4"),
        5: read_three_numbers("Frequency 5")
    }
    st.DEFAULT_POC = value
    st.save()

@set.command()
@click.argument("path", required=False)
def SATELLITES(path) -> None:
    """Update satellites .atx path"""
    st = Settings()
    print(f"Current value: {st.SATELLITES}")
    if path is None:
        path = Path(input("Enter new value: "))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File {path} not found.")
    if not verify_atx(path):
        raise ValueError(f"File {path} is not a valid ATX file")
    st.SATELLITES = path
    st.save()

@click.group()
def clear() -> None:
    """Clear Settings value"""
    pass

@clear.command()
def RTKP_CONFIG() -> None:
    """Clear RTKP config file path"""
    st = Settings()
    st.RTKP_CONFIG = None
    st.save()

@clear.command()
def DATA_DIRS() -> None:
    """Clear DATA_DIRS (path where data directories are generated, defaults to $HOME/Radar/Data)"""
    st = Settings()
    st.DATA_DIRS = None
    st.save()

@clear.command()
def PROCESSING_DIRS() -> None:
    """Clear PROCESSING_DIRS (path where processing directories are generated, defaults to $HOME/Radar/Processing)"""
    st = Settings()
    st.PROCESSING_DIRS = None
    st.save()

@clear.command()
def TOMO_DIRS() -> None:
    """Clear TOMO_DIRS (path where tomogram directories are generated, defaults to $HOME/Radar/Tomograms)"""
    st = Settings()
    st.TOMO_DIRS = None
    st.save()

@clear.command()
def SWEPOS_USERNAME():
    """Clear Swepos username"""
    st = Settings()
    st.SWEPOS_USERNAME = None
    st.save()

@clear.command()
def SWEPOS_PASSWORD():
    """Clear Swepos password"""
    st = Settings()
    st.SWEPOS_PASSWORD = None
    st.save()

@clear.command()
def SATELLITES():
    """Clear satellite ATX file"""
    st = Settings()
    st.SATELLITES = None
    st.save()

@click.group()
def add() -> None:
    """Add files or folders to TomoSAR"""
    pass

@add.command()
@click.argument("paths", nargs=-1)
def DEM(paths) -> None:
    """Add DEM files or folders containing DEMs"""
    st = Settings()
    if not paths:
        paths = input("Enter path(s): ").split()
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"{"File" if path.is_file() else "Folder"} not found: {path}")
        if path.is_file() and not path.suffix in (".tif, .tiff"):
            raise ValueError(f"File {path} is not a GeoTIFF file.")
        st.DEMS.append(path.resolve())
    st.save()

@add.command()
@click.argument("paths", nargs=-1)
def CANOPY(paths) -> None:
    """Add CANOPY files or folders containing CANOPIES"""
    st = Settings()
    if not paths:
        paths = input("Enter path(s): ").split()
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"{"File" if path.is_file() else "Folder"} not found: {path}")
        if path.is_file() and not path.suffix in (".tif, .tiff"):
            raise ValueError(f"File {path} is not a GeoTIFF file.")
        st.CANOPIES.append(path.resolve())
    st.save()

@add.command()
@click.argument("paths", nargs=-1)
def MASK(paths) -> None:
    """Add MASK files or folders containing MASKS"""
    st = Settings()
    if not paths:
        paths = input("Enter path(s): ").split()
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"{"File" if path.is_file() else "Folder"} not found: {path}")
        if path.is_file() and not path.suffix in (".shp"):
            raise ValueError(f"File {path} is not a shape file.")
        st.MASKS.append(path.resolve())
    st.save()

@add.command()
@click.argument("antenna_type", required=False)
@click.argument("path", required=False)
@click.option("--radome", help="Radome type", default="NONE")
def RECEIVER(antenna_type: str, path: str, radome: str = "NONE") -> None:
    """Add an antenna file for a receiver"""
    if antenna_type == "SATELLITES":
        raise RuntimeError("Use tomosar set SATELLITES to set the satellites antenna file")
    st = Settings()
    if not antenna_type:
        antenna_type = input("Enter antenna type: ")
    if not path:
        path = input("Enter path: ")
    path = Path(path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if not verify_atx(path):
        raise ValueError(f"File {path} is not a valid ATX file")
    if antenna_type in st.ANTENNAS and radome in st.ANTENNAS[antenna_type]:
        warn(f"Path {st.ANTENNAS[antenna_type]} for receiver ID {antenna_type} {radome} overwritten.")
    elif antenna_type not in st.ANTENNAS:
        st.ANTENNAS[antenna_type] = {}    
    st.ANTENNAS[antenna_type][radome] = path.resolve()
    st.save()

@click.group()
def remove() -> None:
    """Remove files or folders from TomoSAR"""
    pass

@remove.command()
@click.argument("paths", nargs=-1)
def DEM(paths) -> None:
    """Remove DEM path"""
    st = Settings()
    if not paths:
        print("Current DEMS:")
        for dem in st.DEMS:
            print("\t" + dem)
        print()
        paths = input("Enter path(s) to remove: ").split()
    paths = [Path(path).resolve() for path in paths]
    old_dems = st.DEMS
    st.DEMS = [dem for dem in old_dems if not dem in paths]
    st.save()

@remove.command()
@click.argument("paths", nargs=-1)
def CANOPY(paths) -> None:
    """Remove CANOPY path"""
    st = Settings()
    if not paths:
        print("Current CANOPIES:")
        for canopy in st.CANOPIES:
            print("\t" + canopy)
        print()
        paths = input("Enter path(s) to remove: ").split()
    paths = [Path(path).resolve() for path in paths]
    old_canopies = st.CANOPIES
    st.CANOPIES = [canopy for canopy in old_canopies if not canopy in paths]
    st.save()

@remove.command()
@click.argument("paths", nargs=-1)
def MASK(paths) -> None:
    """Remove MASK path"""
    st = Settings()
    if not paths:
        print("Current MASKS:")
        for mask in st.MASKS:
            print("\t" + mask)
        print()
        paths = input("Enter path(s) to remove: ").split()
    paths = [Path(path).resolve() for path in paths]
    old_masks = st.MASKS
    st.MASKS = [mask for mask in old_masks if not mask in paths]
    st.save()

@remove.command()
@click.argument("antenna_type", required=False)
@click.argument("path", required=False)
@click.option("--radome", help="Radome type", default="NONE")
def RECEIVER(antenna_type: str, path: str, radome: str = "NONE") -> None:
    """Remove RECEIVER ID for specified radome (default: NONE)"""
    st = Settings()
    if antenna_type == "SATELLITES":
        raise RuntimeError("Use tomosar clear SATELLITES to remove the satellites antenna file")
    if not antenna_type:
        antenna_type = input("Enter antenna type: ")
    if not path:
        path = input("Enter path: ")
    if antenna_type in st.RECEIVERS:
        st.RECEIVERS[antenna_type].pop(radome, None)
        if not st.RECEIVERS[antenna_type]:
            st.RECEIVERS.pop(antenna_type, None)
    st.save()
    