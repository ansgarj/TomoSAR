# Imports
import os
import argparse
import click

from tomosar import tomoload, interactive_console

@click.group()
def tomoload() -> None:
    """Entry point for tomoload utilities."""
    pass

@tomoload.command()
def interactive():
    parser = argparse.ArgumentParser(
        description="Collect information on all complex .tif files in the path."
    )

    # Positional arguments: input paths
    parser.add_argument(
        "path",
        nargs='?',
        default=".",
        help="Input directory or file to process (default: current directory)."
    )
    
    # Optional flags
    parser.add_argument("-c", "--cached", action="store_true", help="Use cached masks.")

    # Optional parameters
    parser.add_argument("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads.")

    # Parse
    args = parser.parse_args()

    # Call sliceinfo
    tomos = tomoload(path=args.path, cached= args.cached, npar=args.npar)
    interactive_console({"tomos": tomos})
