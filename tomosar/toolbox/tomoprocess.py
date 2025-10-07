#!/usr/bin/env python3
import click

from .processing.trackfinder import trackfinder
from .processing.forge import forge
from .processing.station_ppp import ppp
from .processing.fetch_swepos import swepos

@click.group()
def tomoprocess() -> None:
    """Entry point for tomoprocess utilities."""
    pass

tomoprocess.add_command(trackfinder)
tomoprocess.add_command(forge)
tomoprocess.add_command(ppp)
tomoprocess.add_command(swepos)