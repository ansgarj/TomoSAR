#!/usr/bin/env python3

import argparse
import sys
import os
import pytz

from tomosar.gnss import extract_rnx_info

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract GNSS info and find nearest SWEPOS station.")
    parser.add_argument("filepath", help="Path to the rinex file")


    args = parser.parse_args()
    start_utc, end_utc, pos = extract_rnx_info(args.filepath)
    stockholm_tz = pytz.timezone('Europe/Stockholm')

    if start_utc and end_utc:
        start_local = start_utc.astimezone(stockholm_tz)
        end_local = end_utc.astimezone(stockholm_tz)
        print(f"Start time: {start_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} / {start_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"End time: {end_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} / {end_local.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("No valid timestamps found in the file.")

