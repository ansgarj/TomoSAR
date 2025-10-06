#!/usr/bin/env python3

import os
import argparse
import sys
import code

from tomosar import SliceInfo


script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

### Argument parsing and main function
def load_man():
    """
    Load the manual of the script from a text file.
    
    Returns:
        str: The content of the manual file.
    """
    manual_file = os.path.join(script_dir, "manual.txt")
    if os.path.exists(manual_file):
        with open(manual_file, "r") as f:
            return f.read()
    else:
        return "No description available."
    
def parse_arguments():
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
    parser.add_argument("-r", "--read", action="store_true", help="Also read image data.")
    parser.add_argument("--man", action="store_true", help="Show the manual of the script.")

    # Optional parameters
    parser.add_argument("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads.")

    return parser.parse_args()

def main():
    args = parse_arguments()
    # Print the manual if requested
    if args.man:
        print(load_man())
        sys.exit(0)

    # Call sliceinfo
    slice_info = SliceInfo.scan(path=args.path, read=args.read, npar=args.npar)
    code.interact(local=locals())
    return slice_info

### Script entry point
if __name__ == "__main__":
    main()