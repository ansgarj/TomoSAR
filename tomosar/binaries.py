import shutil
import re
from collections import defaultdict
import json
from importlib.resources import files
import subprocess
from pathlib import Path
import json
from importlib.resources import path as importpath
from contextlib import contextmanager
from typing import Iterator
from contextlib import ExitStack

from .utils import changed, warn
from .config import Settings, LOCAL

# Catch-all run command for binariy executables
def run(cmd: str | list):
    if not isinstance(cmd, list):
        cmd = [cmd]
    binary_name = cmd[0]
    require_binary(binary_name)
    if Settings().VERBOSE:
            print(' '.join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command failed with exit code {e.returncode}.\n"
            f"stdout:\n{e.stdout}\n"
            f"stderr:\n{e.stderr}"
        ) from e

# Check if required binary is installed
def require_binary(name: str, hint: str|None = None) -> str:
    try:
        dep = load_dependencies()[name]
    except:
        raise RuntimeError(f"Failed to find required binary '{name}' in tomosar.setup.dependencies.json")
    path = shutil.which(name)
    if path is None:
        if not hint:
            raise RuntimeError(f"Required binary '{name}' not found in PATH.\n\033[1mSource\033[22m: {dep["Source"]}")
        else:
            raise RuntimeError(f"Required binary '{name}' not found in PATH.\n{hint}")
    return path

def load_dependencies() -> dict[str,dict]:
    path = files("tomosar.setup").joinpath("dependencies.json")
    with open(path) as f:
        return json.load(f)

def check_required_binaries() -> None:
    deps = load_dependencies()
    missing = []
    for name, dep in deps.items():
        try:
            hint = json.dumps(dep, indent=4)
            require_binary(name, hint=hint)
        except RuntimeError as e:
            print(f"[Missing] {e}")
            missing.append(name)
    if missing:
        print(f"{len(missing)} missing binaries: {missing}")
        return
    else:
        print("All required binaries are available.")

def substitute_flags(path: Path, resolved: dict):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r"\{\{(\w+)\}\}")

    def replacer(match):
        return resolved.get(match.group(1), match.group(0))

    substituted = pattern.sub(replacer, content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(substituted)

# Get resource file
@contextmanager
def resolve_resources(keys, resource_func, **kwargs):
    """Context manager that resolves multiple resource keys and keeps them alive."""
    with ExitStack() as stack:
        resolved = {}
        for key in keys:
            try:
                ctx = resource_func(None, key, **kwargs)
                path = stack.enter_context(ctx)
                resolved[key] = str(path) if path else f"{{{{{key}}}}}"
            except Exception as e:
                warn(f"Could not resolve resource for key '{key}': {e}")
                resolved[key] = f"{{{{{key}}}}}"
        yield resolved

@contextmanager
def resource(path: str | Path | None, key: str, **kwargs) -> Iterator[Path]:
    """Provides a temporary local copy of the file specified in path. If path is empty or None,
    provides a temporary local copy of a file specified in settings or fetched internally based on key.

    If no file is provided None is yielded.

    Valid keys: 'SATELLITES', 'SWEPOS_COORDINATES', 'RTKP_CONFIG', 'RECEIVER' 'DEM', 'CANOPY'
    NOTE: RTKP_CONFIG can be called with standard=True to disable demo5 specific options in internal files
    NOTE: RECEIVER takes antenna (required) and radome (optional) keywords
    NOTE: DEM and CANOPY take bounds (required) and res (required) keywords"""
    # Generate a local copy of a file
    def local_copy(file: Path) -> Path:
        if file.exists() and file.is_file():
            tmp_path = Path.cwd() / file.with_suffix(".tmp").name
            shutil.copy2(file, tmp_path)
            return tmp_path
        raise FileNotFoundError(f"{file} not found")
    
    # Prepare tmp_path
    tmp_path = None
    
    # Check if path was specified
    if path:
        path = Path(path)
        if path.exists() and path.is_file():
            tmp_path = local_copy(path)
        else:
            warn(f"Path {path} does not point to a file. Ignoring.")

    # Match against file keys for Settings reference or internal pointers    
    match key:
        case "SATELLITES":
            filename = Settings().SATELLITES
            if filename:
                path = Path(filename)
                if path.exists():
                    tmp_path = local_copy(path)
                else:
                    warn(f"Path {path} read from settings does not point to a file. Ignoring.")
            filename = "igs20_2385.atx"
        case "SWEPOS_COORDINATES":
            filename = "Koordinatlista_2025_10_14.csv"
        case "RTKP_CONFIG":
            filename = Settings().RTKP_CONFIG
            if filename:
                path = Path(filename)
                if path.exists():
                    tmp_path = local_copy(path)
                else:
                    warn(f"Path {path} read from settings does not point to a file. Ignoring.")
            standard = kwargs.get("standard",False)
            if standard:
                filename = "m8t_5hz_standard.conf"
            else:
                filename = "m8t_5hz_demo5.conf"
        case "RECEIVER":
            antenna = kwargs.get("antenna", None)
            if antenna is None:
                raise KeyError("To get a RECEIVER resource, antenna must be specified (antenna=)")
            radome = kwargs.get("radome", "NONE")
            filename = Settings().RECEIVER(receiver_id=antenna, radome=radome)
            if filename:
                path = Path(filename)
                if path.exists():
                    tmp_path = local_copy(path)
                else:
                    warn(f"Path {path} read from settings does not point to a file. Ignoring")
        case "DEM":
            bounds = kwargs.get("bounds", None)
            if bounds is None:
                raise KeyError("To get a DEM resource, bounds must be specified (bounds=)")
            res = kwargs.get("resolution", None)
            if res is None:
                raise KeyError("To get a DEM resource, resolution must be specified (resolution=)")
            vrt_path = LOCAL / "DEM.vrt"
            vrt_path = build_vrt(Settings().DEMS)
            tmp_path = generate_raster(vrt_path)
        case "CANOPY":
            bounds = kwargs.get("bounds", None)
            if bounds is None:
                raise KeyError("To get a CANOPY resource, bounds must be specified (bounds=)")
            res = kwargs.get("resolution", None)
            if res is None:
                raise KeyError("To get a CANOPY resource, resolution must be specified (resolution=)")
            vrt_path = LOCAL / "CANOPY.vrt"
            vrt_path = build_vrt(Settings().CANOPIES)
            tmp_path = generate_raster(vrt_path)

    if tmp_path is None and filename:
        with importpath('tomosar.data', filename) as resource_path:
            # Create a temp file in the current working directory
            tmp_path = local_copy(resource_path)
    
    # Find all {{KEY}} in the file
    with open(tmp_path, 'r', encoding='utf-8') as f:
        content = f.read()
    keys = set(re.findall(r"\{\{(\w+)\}\}", content))

    # Resolve and substitute
    if keys:
        with resolve_resources(keys, resource, **kwargs) as resolved:
            substitute_flags(tmp_path, resolved)
            # Yield temporary local path
            try:
                yield tmp_path
            finally:
                tmp_path.unlink(missing_ok=True)  # Clean up after use
    else:
        # Yield temporary local path
        try:
            yield tmp_path
        finally:
            tmp_path.unlink(missing_ok=True)  # Clean up after use
    
# Named functions for binary executables
def crx2rnx(crx_file: str|Path):
    rnx_path = crx_file.with_suffix('.rnx')
    print(f"Unpacking {crx_file} > {rnx_path} ...", end=" ", flush=True)
    run(['crx2rnx', '-d', crx_file])
    print("done.")
    return rnx_path

def _generate_merged_filenames(files: list[Path]) -> Path|None:
        pattern = re.compile(
            r"^(?P<source>[A-Z0-9]{10})_(?P<datetime>\d{11})_(?P<duration>\d{2}[SMHD])_(?P<freq>\d{2}[SMHD])_(?P<type>[A-Z]+)\.(?P<ext>[A-Z0-9]{3})$"
        )
        units = re.compile(
            r"(?P<number>\d{2})(?P<unit>[SMHD])"
        )
        grouped = defaultdict(set)
        for f in files:
            if (match := pattern.match(f.name)):
                key = (
                    match.group("source"),
                    match.group("freq"),
                    match.group("type"),
                    match.group("duration"),
                    match.group("ext")
                )
                grouped[key].add(int(match.group("datetime")))

        descriptive_filenames = []
        for (source, frequency, type, duration, ext), datetimes in grouped.items():
            datetime = min(datetimes)
            if (match := units.match(duration)):
                dur = int(match.group("number"))
                dur_unit = match.group("unit")
            else:
                raise RuntimeError(f"Failed to parse filenames: {files}")
            no_files = len(datetimes)
            dur = dur * no_files
            if type.endswith("O"):
                # Observation file:
                out_type = "MO"
            elif type.endswith("N"):
                # Navigation data file
                out_type = "MN"
            elif type == "ORB" or type == "CLK":
                # Ephemeris file
                out_type = type
            merged_filename = files[0] / f"{source}_{datetime}_{dur:02}{dur_unit}_{frequency}_{out_type}.{ext}"
            descriptive_filenames.append(merged_filename)
        if len(descriptive_filenames) > 1:
            raise RuntimeError(f"Unable to merge files due to conflicting sources, frequencies, durations, types or extensions. Merging aborted. Files: {files}")
        return descriptive_filenames[0] if descriptive_filenames else None

def merge_rnx(rnx_files: list[str|Path], force: bool = False):
    merged_file = _generate_merged_filenames(rnx_files)
    if merged_file and merged_file.exists() and not force:
        print(f"Discovered merged file {merged_file}. Aborting merge of RNX files.")
    print(f"Merging observation files > {merged_file} ...", end=" ", flush=True)
    run(["gfzrnx", "-q", "-finp"] + [f for f in rnx_files] + ["-fout", merged_file])
    print("done.")
    return merged_file

def merge_eph(eph_files: list[str|Path], force: bool = False):
    eph_files = [Path(f) for f in eph_files]
    # Get .SP3 files
    sp3_files = [f for f in eph_files if f.suffix == ".SP3"]
    # Merge
    merged_sp3 = _generate_merged_filenames(sp3_files)
    if merged_sp3 and  merged_sp3.exists() and not force:
        print(f"Discovered merged file {merged_sp3}. Aborting merge of .SP3 files.")
    print(f"Merging .SP3 files > {merged_sp3} ...", end=" ", flush=True)
    with merged_sp3.open("w", encoding="utf-8") as out_file:
        for file_path in sp3_files:
            with Path(file_path).open("r", encoding="utf-8") as in_file:
                for line in in_file:
                    out_file.write(line)
    print("done.")

    # Get .CLK files
    clk_files = [f for f in eph_files if f.suffix == ".CLK"]
    # Merge
    merged_clk = _generate_merged_filenames(clk_files)
    if merged_clk and  merged_clk.exists() and not force:
        print(f"Discovered merged file {merged_clk}. Aborting merge of .CLK files.")
    print(f"Merging .CLK files > {merged_clk} ...", end=" ", flush=True)
    with merged_clk.open("w", encoding="utf-8") as out_file:
        for file_path in clk_files:
            with Path(file_path).open("r", encoding="utf-8") as in_file:
                for line in in_file:
                    out_file.write(line)
    print("done.")

    return merged_sp3, merged_clk

def ubx2rnx(ubx_file: str|Path):
    sbs_path = ubx_file.with_suffix(".sbs")
    nav_path = ubx_file.with_suffix(".nav")
    obs_path = ubx_file.with_suffix(".obs")
    run(["convbin", "-r", "ubx", "-od", "-os", "-o", ubx_file])
    return obs_path, nav_path, sbs_path

def rnx2rtkp(
        rover_obs: str|Path,
        base_obs: str|Path,
        nav_file: str|Path,
        config: str|Path,
        out_path: str|Path,
        mocoref_file: str|Path = None,
        sbs_file: str|Path = None
) -> None:
    cmd = ['rnx2rtkp', '-k', config, '-o', out_path]
    if mocoref_file:
        with open(mocoref_file, 'r') as f:
            mocoref = json.load(f)
        print(f"mocoref: {mocoref}")
        h = mocoref["h"] - 0.2
        cmd.extend(["-l", str(mocoref["lat"]), str(mocoref["lon"]), str(h)])
    cmd.extend([rover_obs, base_obs, nav_file])
    if sbs_file:
        cmd.append(sbs_file)
    print(f"Running RTKP post processing on rover {rover_obs} with base {base_obs} ...", end=" ", flush=True)
    try: 
        run(cmd)
    except RuntimeError:
        with resource(None, "RTKP_CONFIG", standard=True) as new_config:
            cmd[2] = new_config
            run(cmd)
    print("done.")

def _ant_type(rinex_path) -> tuple[None|str, None|str]:
    with open(rinex_path, 'r') as f:
        for line in f:
            if 'ANT # / TYPE' in line:
                # ANT TYPE is typically in columns 21–40
                ant_type = line[20:40].strip()
                # Radome is typically in columns 41–60, but may be missing
                radome = line[40:60].strip() or "NONE"
                return ant_type, radome
    return None, None

def ppp(
        obs_file: str|Path,
        sp3_file: str|Path,
        clk_file: str|Path,
        out_path: str|Path,
        navglo_file: str|Path = None,
        atx_file: str|Path = None,
        antrec_file: str|Path = None
    ) -> None:
    with resource(atx_file, "SATELLITES") as atx:
        antenna_type, radome = _ant_type(obs_file)
        with resource(antrec_file, antenna=antenna_type, radome=radome) as receiver:
            if navglo_file:
                cmd = [
                    'glab',
                    '-input:obs', obs_file,
                    '-input:navglo', navglo_file,
                    '-input:ant', atx.name,
                    '-input:antrec', receiver.name,
                    '-input:orb', sp3_file,
                    '-input:clk', clk_file,
                    '-model:recphasecenter', "1", "0", "0", "0.9",
                    '-model:recphasecenter', "2", "0", "0", "0.9",
                    '-model:recphasecenter', "3", "0", "0", "0.9",
                    '-model:recphasecenter', "4", "0", "0", "0.9",
                    '-model:recphasecenter', "5", "0", "0", "0.9",
                ]
            else:
                cmd = [
                    'glab',
                    '-input:obs', obs_file,
                    '-input:ant', atx.name,
                    '-input:orb', sp3_file,
                    '-input:clk', clk_file,
                    #'-filter:backward', 
                    '-model:recphasecenter', "1", "0", "0", "0.9",
                    '-model:recphasecenter', "2", "0", "0", "0.9",
                    '-model:recphasecenter', "3", "0", "0", "0.9",
                    '-model:recphasecenter', "4", "0", "0", "0.9",
                    '-model:recphasecenter', "5", "0", "0", "0.9",
                ]
            print(f"Running station PPP on {obs_file} > {out_path} ...", end=" ", flush=True)
            result = run(cmd)
            out_path.write_text(result.stdout)
            print("done. ")

# VRT
def build_vrt(vrt_path: Path|str, paths: list[Path|str]) -> Path:
    """
    Build a .vrt mosaic from all .tif files, returning the file path if a single GeoTIFF file is passed
    """
    tif_files = []
    for path in paths:
        path = Path(path)
        if path.is_file() and path.suffix in (".tif", ".tiff"):
            tif_files.append(path)
        else:
            new_files = list(path.rglob("*.tif"))
            new_files.extend(list(path.rglob(".tiff")))
            tif_files.extend(new_files)
    if not tif_files:
        raise FileNotFoundError(f"No GeoTIFF files found in {paths}")
    if len(tif_files) == 1:
        return tif_files[0]
    
    # Check if the current VRT matches input files and build new VRT otherwise
    vrt_path = Path(vrt_path)
    hash_path = vrt_path.with_suffix(".hash")
    if changed(hash_path, tif_files):
        print("Building new VRT ...", end=" ", flush=True)
        cmd = ["gdalbuildvrt", "-resolution", "highest", str(vrt_path)] + [str(f) for f in tif_files]
        run(cmd)

def generate_raster(
        vrt_path: Path|str,
        bounds: tuple[float, float, float, float],
        res: tuple[float, float]
    ) -> None:

    out_path = Path.cwd() / Path(vrt_path).with_suffix(".tmp").name
    cmd = ["gdalwarp", "-te", *bounds, "-tr", *res, "-r", "average", "-of", "GTiff", vrt_path, out_path]
    run(cmd)
    return out_path