# Imports
import os
import click
from pathlib import Path

from .. import tomoload, SliceInfo
from ..utils import interactive_console

@click.command()
@click.argument("path", required=False, default='.', type=click.Path(exists=True, path_type=Path))
@click.option("-u", "--update", is_flag=True, help="Update cached masks")
@click.option("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads for file reading")
def load(path: Path, update: bool, npar: int) -> None:
    """Loads a TomoScenes object into a Python terminal"""
    cached = not update
    # Call sliceinfo
    tomos = tomoload(path=path, cached=cached, npar=npar)
    interactive_console({"tomos": tomos})

@click.command()
@click.argument("path", required=False, default='.', type=click.Path(exists=True, path_type=Path))
@click.option("-r", "--read", is_flag=True, help="Also read image data.")
@click.option("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads for file reading.")
def sliceinfo(path: Path, read: bool, npar: int):
    """Loads a SliceInfo object into a Python terminal"""
    # Call sliceinfo
    slices = SliceInfo.scan(path=path, read=read, npar=npar)
    interactive_console({"slices": slices})