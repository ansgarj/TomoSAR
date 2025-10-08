# Imports
import os
import click
from pathlib import Path

from tomosar import tomoload, SliceInfo
from tomosar.utils import interactive_console

@click.command()
@click.argument("path", required=False, default='.', type=click.Path(exists=True, path_type=Path))
@click.option("-c", "--cached", is_flag=True, help="Use cached masks")
@click.option("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads for file reading")
def load(path: Path, cached: bool, npar: int) -> None:

    # Call sliceinfo
    tomos = tomoload(path=path, cached= cached, npar=npar)
    interactive_console({"tomos": tomos})

@click.command()
@click.argument("path", required=False, default='.', type=click.Path(exists=True, path_type=Path))
@click.option("-r", "--read", is_flag=True, help="Also read image data.")
@click.option("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads for file reading.")
def sliceinfo(path: Path, read: bool, npar: int):

    # Call sliceinfo
    slices = SliceInfo.scan(path=path, read=read, npar=npar)
    interactive_console({"slices": slices})