#!/usr/bin/env python3
import click

from .check_binaries import check_required_binaries

@click.group()
def tomotest() -> None:
    """Entry point for tomotest utilities."""
    pass

@tomotest.command()
def binaries() -> None:
    """Look for required binaries."""
    check_required_binaries()

# Below are placeholders
@tomotest.command()
def data() -> None:
    """Generate tomotest data."""
    click.echo("Generating tomotest data...")

@tomotest.command()
def stats() -> None:
    """Compute tomotest statistics."""
    click.echo("Computing statistics...")

if __name__ == '__main__':
    tomotest()