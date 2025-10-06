#!/usr/bin/env python3
import click
from pathlib import Path

from tomosar import station_ppp

@click.command()
@click.argument("data_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-a", "--atx", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the antenna .atx file")
@click.option("-r", "--receiver", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the .atx file containing receiver antenna info")
@click.option("--downloads", type=int, default=10, help="Max number of parallel downloads (default: 10)")
@click.option("--attempts", type=int, default=3, help="Max number of attempts for each file (default: 3)")
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None, help="Output directory for SWEPOS rinex files")
@click.option("-d", "--dry", is_flag=True, help="Dry run without downloads")
@click.option("--cont", is_flag=True, help="Continue run after downloads complete")
@click.option("-x", "--header", is_flag=True, default=True, help="Modify OBS file header with new position (default: True)")
def ppp(data_dir, atx, receiver, downloads, attempts, output, dry, cont, header) -> None:
    """Extract GNSS info and find nearest SWEPOS station."""
    station_ppp(
        data_dir=data_dir,
        atx_path=atx,
        antrec_path=receiver,
        max_downloads=downloads,
        max_retries=attempts,
        dry=dry,
        output_dir=output,
        cont=cont,
        header=header
    )
