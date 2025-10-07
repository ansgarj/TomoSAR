#!/usr/bin/env python3

import os
import argparse

from tomosar import SliceInfo, interactive_console
    
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

    # Optional parameters
    parser.add_argument("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads.")

    return parser.parse_args()

def main():
    args = parse_arguments()

    # Call sliceinfo
    slices = SliceInfo.scan(path=args.path, read=args.read, npar=args.npar)
    interactive_console({"slices": slices})

    # pink = "\033[95m"
    # reset = "\033[0m"
    # bold = "\033[1m"
    # normal = "\033[22m"
    # sys.ps1 = "\033[95m>>> \033[0m"  # Light magenta (Python pink)
    # sys.ps2 = "\033[95m... \033[0m"
    # print(f"{pink}{bold}Printing loaded variables ...")
    # code.interact(banner=f"{pink}{bold}slices: {normal}{slices}{reset}", local=locals())

### Script entry point
if __name__ == "__main__":
    main()