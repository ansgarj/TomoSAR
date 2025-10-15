import click
from .. import ubx2rnx, rnx2rtkp
from ..gnss import fetch_swepos, station_ppp

@click.group()
def tomotest() -> None:
    """Entry point for tomotest utilities."""
    pass

@tomotest.command()
def gnss() -> None:
    """Test GNSS processing capabilities."""
    pass # Placeholder

# Below are placeholders
@tomotest.command()
def data() -> None:
    """Generate tomotest data."""
    click.echo("Generating tomotest data...")

@tomotest.command()
def stats() -> None:
    """Compute tomotest statistics."""
    click.echo("Computing statistics...")