import laspy
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path
import rasterio 
from pyproj import Transformer
import xml.etree.ElementTree as ET
import os

from .utils import leap_seconds, warn
from .config import Settings, LOCAL
from .manager import build_vrt
from .position import Pos

# Get elevation from DEMs for a point
def elevation(point: Pos, dem_path: Path|str = None) -> float | None:
    """Returns the elevation for a specific point from the highest resolved DEM at that point,
    or from the user specified DEM."""
    def  get_elevation(dem_path: Path) -> float|None:
        def _check_file_type(filename: Path) -> str:
            ext = filename.suffix.lower()
            if ext in [".tif", ".tiff"]:
                return "TIFF"
            elif ext == ".vrt":
                return "VRT"
            else:
                return "Unknown"
        
        def _point_in_bounds(src: rasterio.DatasetReader) -> tuple[float, float]|None:
            match src.crs:
                case point.frame.proj_crs(lat=point.lat, lon=point.lon):
                    x, y = point.easting[0], point.northing[0]
                case point.frame.geo_crs:
                    x, y = point.lon[0], point.lat[0]
                case _:
                    try:
                        x, y = Transformer.from_crs(point.frame.geo_crs, src.crs, always_xy=True).transform(point.lon[0], point.lat[0])    
                    except Exception:
                        return None
            if src.bounds.left <= x <= src.bounds.right and src.bounds.bottom <= y <= src.bounds.top:
                return (x,y)
            return None

        def _normalize_path(path: Path) -> Path:
            """
            Normalize a path string:
            - Expand environment variables and user home (~)
            - Resolve symlinks if it's a real filesystem path
            - Leave GDAL virtual paths (/vsizip/, /vsicurl/, etc.) untouched
            """
            path_str = str(path)
            if path_str.startswith("/vsi"):  # GDAL virtual path
                return path_str
            # Expand environment variables and ~
            expanded = os.path.expandvars(os.path.expanduser(path_str))
            # Resolve if possible
            return Path(expanded).resolve()

        def _find_raster_in_vrt(vrt_path: Path) -> tuple[str|None, tuple[float,float]|None]:
            tree = ET.parse(vrt_path)
            root = tree.getroot()

            for source in root.iter("SourceFilename"):
                raster_name = source.text.strip()
                relative = source.attrib.get("relativeToVRT", "1") == "1"

                # Compute full path
                if relative:
                    raster_path = vrt_path.resolve().parent / raster_name
                else:
                    raster_path = Path(raster_name)

                # Normalize path (handles env vars, symlinks, GDAL paths)
                full_path = _normalize_path(raster_path)

                try:
                    with rasterio.open(full_path) as src:
                        coords = _point_in_bounds(src)
                        if coords:
                            return full_path, coords
                except Exception:
                    continue

            return None, None

        # Begin get_dem function
        file_type = _check_file_type(dem_path)
        if file_type == "TIFF":
            with rasterio.open(dem_path) as src:
                coords = _point_in_bounds(src)
                if coords:
                    dem = src.read(1)
                    return dem[coords]
                else:
                    return None
        
        elif file_type == "VRT":
            raster_path, coords = _find_raster_in_vrt(dem_path)
            if raster_path:
                with rasterio.open(raster_path) as src:
                    dem = src.read(1)
                    return dem[coords]
            else:
                return None
        
        else:
            return None
    
    # Begin main function
    dem_path = Path(dem_path)
    if dem_path.is_file():
        result = get_elevation(dem_path)
    else:
        settings = Settings()
        vrt_path = LOCAL / f"{settings.TARGET_FRAME}_DEM.vrt"
        dem_path = build_vrt(vrt_path, settings.DEMS)
        
        result = get_elevation(dem_path)    
    if not result:
        warn(f"No DEM found for coordinates {point}")

    return result

 
def las_acquisition_time(las_path: str, reference_date: datetime) -> datetime:
    """
    Extract median acquisition timestamp from LAS file using GPS time.
    Auto-detects GPS time format and converts to UTC.

    Returns:
    - epoch as fractional year
    """
    las = laspy.read(las_path)
    gps_times = las.gps_time
    if gps_times.size == 0:
        raise ValueError("No GPS time data found in LAS file.")
    
    gps_median = float(np.median(gps_times))
    gps_epoch = datetime(1980, 1, 6)
    expected_abs = (reference_date - gps_epoch).total_seconds()

    # Detect format
    if gps_median > 1e9:
        # Absolute GPS time
        naive_time = gps_epoch + timedelta(seconds=gps_median)
        fmt = "absolute"
    elif gps_median < 604800:
        # Seconds-of-week
        gps_week = int((reference_date - gps_epoch).days // 7)
        gps_week_start = gps_epoch + timedelta(weeks=gps_week)
        naive_time = gps_week_start + timedelta(seconds=gps_median)
        fmt = "seconds-of-week"
    else:
        # Check for vendor offset (e.g., minus 1e9)
        diff = abs(expected_abs - gps_median)
        if abs(diff - 1e9) < 5e7:  # tolerance ~50 million seconds (~1.5 years)
            naive_time = gps_epoch + timedelta(seconds=gps_median + 1e9)
            fmt = "offset(+1e9)"
        else:
            raise ValueError(f"Unknown GPS time format: median={gps_median}, diff={diff}")
    
    # Apply leap second correction
    utc_time = naive_time - timedelta(seconds=leap_seconds(naive_time))
    utc_time = utc_time.replace(tzinfo=timezone.utc)

    # Convert to fractional year
    year = utc_time.year
    start_of_year = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_of_year = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    year_length = (end_of_year - start_of_year).total_seconds()
    seconds_into_year = (utc_time - start_of_year).total_seconds()

    epoch = year + seconds_into_year / year_length

    # Optional: print detected format for debugging
    # print(f"Detected GPS time format: {fmt}")
    
    return epoch

