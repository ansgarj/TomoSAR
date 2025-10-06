#!/usr/bin/env python3
import click
from pathlib import Path

from tomosar import fetch_swepos

@click.command()
@click.argument("filepath", type=click.Path(exists=True, path_type=Path))
@click.option("--stations", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the SWEPOS coordinate list CSV")
@click.option("--downloads", type=int, default=10, help="Max number of parallel downloads (default: 10)")
@click.option("--attempts", type=int, default=3, help="Max number of attempts for each file (default: 3)")
@click.option("-o", "--output", type=click.Path(path_type=Path), default="SWEPOS", help="Output directory for SWEPOS RINEX files")
@click.option("-d", "--dry", is_flag=True, help="Dry run without downloads")
@click.option("--cont", is_flag=True, help="Continue run after downloads complete")
@click.option("-g","--navglo", is_flag=True, help="Also fetch navglo files.")
def swepos(filepath, stations, downloads, attempts, output, dry, cont, navglo) -> None:
    """Extract GNSS info and find nearest SWEPOS station.
    Then download files into output directory."""
    fetch_swepos(
        filepath=filepath,
        stations_path=stations,
        max_downloads=downloads,
        max_retries=attempts,
        dry=dry,
        output_dir=output,
        cont=cont
    )