import click

@click.group()
def tomotest() -> None:
    """Entry point for tomotest utilities."""
    pass

# Below are placeholders
@tomotest.command()
def data() -> None:
    """Generate tomotest data."""
    click.echo("Generating tomotest data...")

@tomotest.command()
def stats() -> None:
    """Compute tomotest statistics."""
    click.echo("Computing statistics...")