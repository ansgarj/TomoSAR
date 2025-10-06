#!/usr/bin/env python3

import click
from pathlib import Path
from tomosar import trackfinder as run_trackfinder

@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("-l", "--linear", type=int, default=None, help="Specify linear track index to modify radar-[...].inf (0 for spiral flights)")
@click.option("-v", "--verbose", is_flag=True, help="Print detailed output")
@click.option("-d", "--dry", is_flag=True, help="Don't save or modify files")
@click.option("-s", "--simple", is_flag=True, help="Skip full analysis")
@click.option("--dem", type=click.Path(exists=True, path_type=Path), default=None, help="Path to DEM file or folder to combine with DEMS_GROUND")
@click.option("--npar", type=int, default=None, help="Number of parallel processes (default: CPU count)")
def trackfinder(path, linear, verbose, dry, simple, dem, npar) -> None:
    """Run trackfinder on a .moco file."""
    run_trackfinder(
        path=path,
        dem_path=dem,
        linear=linear,
        verbose=verbose,
        dry=dry,
        simple=simple,
        npar=npar
    )
