import os
import subprocess
from pathlib import Path
import rasterio
from rasterio.io import DatasetReader
from xml.etree import ElementTree as ET
import numpy as np
from pyproj import Transformer
from dataclasses import dataclass, field
from rasterio.profiles import Profile
from rasterio.features import rasterize
from collections import defaultdict
import geopandas as gpd
from datetime import datetime
import socket

from .utils import warn

### Handling masks
@dataclass
class Mask:
    name: str = ""
    id: int = 0
    mask: np.ndarray = field(default=None, repr=False)
    multilooked: np.ndarray = field(default=None, repr=False)
    metadata: dict = field(default_factory=dict)

    def copy(self) -> 'Mask':
        new_mask = Mask(name=self.name)
        new_mask.mask = self.mask.copy() if self.mask is not None else None
        return new_mask
    
    def apply(self, tomogram: np.ndarray, multilooked: bool = False) -> np.ndarray:
        masked_tomogram = tomogram.copy()
        if multilooked:
            mask = np.broadcast_to(self.multilooked[np.newaxis, :, :], tomogram.shape)
        else:
            mask = np.broadcast_to(self.mask[np.newaxis, :, :], tomogram.shape)
        if np.iscomplexobj(tomogram):
            masked_tomogram[~mask] = np.nan + np.nan*1j
        else:
            masked_tomogram[~mask] = np.nan

        return masked_tomogram

def get_masks(raster_profile: Profile, multilooked_profile: Profile, 
              mask_dir: str | Path = "") -> dict[str,list[Mask]]:
    """
    Generate binary masks from shapefiles using rasterio and geopandas.

    Parameters:
    - mask_dirs: list of directories containing .shp files
    - raster_profile: rasterio profile dictionary (contains raster size, dtype, etc.)
    - raster_transform: rasterio transform object

    Returns:
    - List of dictionaries with keys 'mask' (binary np.ndarray) and 'name' (shapename)
    """
    if not mask_dir:
        mask_paths = _find_masks()
    else:
        mask_paths = _find_masks(mask_dir)
    masks = defaultdict(list)

    for path in mask_paths:
        # Find all .shp files in the directory
        shapefiles = path.glob("*.shp")

        for shp_path in shapefiles:
            # Read shapefile using geopandas
            gdf = gpd.read_file(shp_path)
            shapename = shp_path.stem

            # Loop through each shape in the shapefile
            for idx, row in gdf.iterrows():
                geometry = row.geometry

                # Create a binary mask using rasterio.features.rasterize
                mask = rasterize(
                    [(geometry, 1)],
                    out_shape=(raster_profile['height'], raster_profile['width']),
                    transform=raster_profile['transform'],
                    fill=0,
                    dtype='uint8'
                ).astype(bool)

                if not np.any(mask):
                    continue        # This shape does not intersect raster

                # Create multilooked binary mask
                multilooked = rasterize(
                    [(geometry, 1)],
                    out_shape=(multilooked_profile['height'], multilooked_profile['width']),
                    transform=multilooked_profile['transform'],
                    fill=0,
                    dtype='uint8'
                ).astype(bool)

                # Generate a shapename
                shape_id = row.get('id', idx)

                # Generate metadata
                metadata = {
                    'source': shp_path,
                    'shape_id': shape_id,
                    'timestamp': datetime.now().isoformat(timespec='seconds'),
                    'bounding_box': geometry.bounds,
                    'generated_on': socket.gethostname(),
                    'profile': str(raster_profile),
                    'multilooked': str(multilooked_profile)
                }

                # Append the mask and name to the list
                masks[shapename].append(Mask(name=shapename, id=shape_id, mask=mask, 
                                             multilooked=multilooked, metadata=metadata))

    return masks

def _find_masks(folder: str | Path = "") -> list[Path]:
    """
    Determine the list of mask directories based on environment variable and optionally an additional user input path.

    Returns:
        list of Paths to mask directories.
    """
    env_mask = [Path(p) for p in os.getenv("TOMOMASKS", "").split(os.pathsep)]
    if not folder:
        if env_mask:
            masks = env_mask
        else:
            warn("\nTOMOMASKS environment variable not set, using current working directory.")
            masks = [Path(os.getcwd())]
    else:
        if env_mask:
            masks = env_mask.append(Path(folder))
        else:
            warn("\nTOMOMASKS environment variable not set, using only user specified path.")
            masks = [Path(folder)]

    return masks

### Handling DEM
# Get the correct DEM path
def find_dem(user_dem: str = "", dem_type: str = "ground") -> Path:
    """
    Determine the correct DEM path from user input and environment variables.
    
    Parameters:
        results (dict): Parsed arguments, expected to contain 'DEM'.
        dem_type (str): Either 'ground' or 'canopy'.
    
    Returns:
        str: Path to the DEM .vrt file.
    """
    env_var = "TOMODEMS" if dem_type == "ground" else "TOMOCANOPIES"
    
    if not user_dem:
        dem_paths = [Path(p) for p in os.getenv(env_var, ".").split(os.pathsep)]
        if dem_paths[0] == ".":
            warn(f"\n{env_var} environment variable not set, using current folder.")
    else:
        dem_paths = [Path(p) for p in os.getenv(env_var, "").split(os.pathsep)]
        if dem_paths[0] == "":
            warn(f"\n{env_var} environment variable not set, using only user specified path.")
        dem_paths.append(Path(user_dem))

    return _resolve_dem_path(dem_paths)

def _resolve_dem_path(dem_paths: list[Path]) -> Path:
    """
    Resolve the DEM path, building a .vrt mosaic if necessary.
    """
    if len(dem_paths) == 1:
        dem_path = dem_paths[0]
        if dem_path.is_file():
            return dem_path
        vrt_path = dem_path.with_suffix(".vrt")
        if vrt_path.is_file():
            if vrt_path.stat().st_mtime > dem_path.stat().st_mtime:
                return vrt_path
            else:
                return _build_vrt(dem_path)
        else:
            return _build_vrt(dem_path)
    else:
        return _build_vrt(dem_paths)

def _build_vrt(folders: Path | list[Path]) -> Path:
    """
    Build a .vrt mosaic from all .tif files in the folder.
    """
    if isinstance(folders, Path):
        tif_files = list(folders.glob("*.tif"))
        folders = [folders]
    else:
        tif_files = []
        for path in folders:
            new_files = list(path.glob("*.tif"))
            tif_files.expand(new_files)
    if not tif_files:
        raise FileNotFoundError(f"No .tif files found in {folders}")

    vrt_path = folders[0].with_suffix(".vrt")
    cmd = ["gdalbuildvrt", "-resolution", "highest", str(vrt_path)] + [str(f) for f in tif_files]
    print(f"\nUpdating DEM mosaic: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return vrt_path

# Get DEM
def get_dem(dem_path: Path, lat: float, lon: float) -> tuple[np.ndarray, DatasetReader | None]:
    """
    Load DEM data and its spatial reference if the given lat/lon is within bounds.
    
    Parameters:
        dem_path (str or Path): Path to the DEM file (.tif or .vrt).
        lat (float): Latitude of the point.
        lon (float): Longitude of the point.
    
    Returns:
        Tuple of (DEM array, raster reference or empty dict).
    """
    file_type = _check_file_type(dem_path)

    if file_type == "TIFF":
        with rasterio.open(dem_path) as src:
            if _point_in_bounds(src, lat, lon):
                dem = src.read(1)
                return dem, src
            else:
                return np.array([]), None
    
    elif file_type == "VRT":
        raster_path = _find_raster_in_vrt(dem_path, lat, lon)
        if raster_path:
            with rasterio.open(raster_path) as src:
                dem = src.read(1)
                return dem, src
        else:
            return np.array([]), None
    
    else:
        return np.array([]), None

def _check_file_type(filename: Path) -> str:
    ext = filename.suffix.lower()
    if ext in [".tif", ".tiff"]:
        return "TIFF"
    elif ext == ".vrt":
        return "VRT"
    else:
        return "Unknown"

def _point_in_bounds(src: DatasetReader, lat: float, lon: float) -> bool:
    bounds = src.bounds
    try:
        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        return bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top
    except Exception:
        return False

def _find_raster_in_vrt(vrt_path: Path, lat: float, lon: float) -> str | None:
    tree = ET.parse(vrt_path)
    root = tree.getroot()
    for source in root.iter("SourceFilename"):
        raster_name = source.text
        raster_path = vrt_path.parent / raster_name
        try:
            with rasterio.open(raster_path) as src:
                if _point_in_bounds(src, lat, lon):
                    return str(raster_path)
        except Exception:
            continue
    return None
