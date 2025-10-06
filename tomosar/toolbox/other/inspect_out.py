#!/usr/bin/env python3

import argparse
import sys
import os

from tomosar.gnss import read_out_file

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract GNSS info and find nearest SWEPOS station.")
    parser.add_argument("filepath", help="Path to out file")
    


    args = parser.parse_args()
    read_out_file(
        file_path=args.filepath,
        verbose=True
    )
