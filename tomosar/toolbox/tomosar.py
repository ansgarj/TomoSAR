from importlib.metadata import version as get_version
import click

from .setup_tools import dependencies, setup, warmup
from .interact_tools import load, sliceinfo
from .dev_tools import rnx_info, read_imu, inspect_out, compare_rtkp

@click.group()
def tomosar() -> None:
    """Entry point for TomoSAR meta tools"""
    pass

@tomosar.command()
def version() -> None:
    """Print TomoSAR version"""
    print(f"TomoSAR version: {get_version('tomosar')}")

tomosar.add_command(setup)
tomosar.add_command(dependencies)
tomosar.add_command(warmup)
tomosar.add_command(sliceinfo)
tomosar.add_command(load)

# Dev tools
@tomosar.group(hidden=True)
def dev() -> None:
    """Entry point for dev tools"""
    pass

dev.add_command(rnx_info)
dev.add_command(read_imu)
dev.add_command(inspect_out)
dev.add_command(compare_rtkp)