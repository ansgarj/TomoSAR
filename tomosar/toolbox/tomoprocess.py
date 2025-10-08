import click

from .processing_tools import forge, trackfinder, ppp, swepos

@click.group()
def tomoprocess() -> None:
    """Entry point for tomoprocess utilities."""
    pass

tomoprocess.add_command(trackfinder)
tomoprocess.add_command(forge)
tomoprocess.add_command(ppp)
tomoprocess.add_command(swepos)