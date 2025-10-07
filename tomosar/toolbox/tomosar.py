from importlib.metadata import version as get_version
import click

@click.group()
def tomosar() -> None:
    """Entry point for TomoSAR installation info."""
    pass

@tomosar.command()
def version() -> None:
    """Print TomoSAR version"""
    print(f"TomoSAR version: {get_version('tomosar')}")