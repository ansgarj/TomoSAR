import click
from rich.console import Console
from rich.markdown import Markdown

from .. import __version__
from ..config import PROJECT_PATH
from .setup_tools import dependencies, setup, warmup
from .settings_tools import settings, default, verbose, add, set
from .interact_tools import load, sliceinfo
from .dev_tools import rnx_info, read_imu, inspect_out, compare_rtkp

@click.group()
def tomosar() -> None:
    """Entry point for TomoSAR meta tools"""
    pass

@tomosar.command()
def version() -> None:
    """Print TomoSAR version"""
    print(f"TomoSAR version: {__version__}")

@tomosar.command()
def help() -> None:
    """Prints the Docs/HELPFILE.md file"""

    with open(PROJECT_PATH / "Docs" / "HELPFILE.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Create a console and render the markdown
    console = Console()
    markdown = Markdown(readme_content)
    console.print(markdown)

tomosar.add_command(setup)
tomosar.add_command(dependencies)
tomosar.add_command(warmup)
tomosar.add_command(sliceinfo)
tomosar.add_command(load)
tomosar.add_command(settings)
tomosar.add_command(default)
tomosar.add_command(verbose)
tomosar.add_command(set)
tomosar.add_command(add)

# Dev tools
@tomosar.group(hidden=True)
def dev() -> None:
    """Entry point for dev tools"""
    pass

dev.add_command(rnx_info)
dev.add_command(read_imu)
dev.add_command(inspect_out)
dev.add_command(compare_rtkp)