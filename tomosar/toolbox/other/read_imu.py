#!/usr/bin/env python3
import csv
import argparse
import sys
import os
import matplotlib.pyplot as plt
from pathlib import Path
import csv
import struct


script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

def extract_imu_to_csv(bin_filename: str | Path, csv_filename: str | Path, num_samples: int = None):
    labels = [
        "anglvel_x (deg/s)", "anglvel_y (deg/s)", "anglvel_z (deg/s)",
        "accel_x (g)", "accel_y (g)", "accel_z (g)",
        "channel_7 (raw)", "channel_8 (raw)"
    ]
    rows = []
    with open(bin_filename, "rb") as binfile, open(csv_filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(labels)

        count = 0
        while True:
            if num_samples is not None and count >= num_samples:
                break
            sample = binfile.read(32)
            if len(sample) < 32:
                break
            # Unpack 8 little-endian floats
            row = list(struct.unpack('<8f', sample))
            writer.writerow([f"{v:.6f}" for v in row])
            rows.append(row)
            count += 1
    return rows, labels


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract GNSS info and find nearest SWEPOS station.")
    parser.add_argument("file", help="Path to the directory containing OBS and NAV files")

    parser.add_argument("-n", "--num", type=int, help="Number of samples to read", default=None)


    args = parser.parse_args()

    imu_file = Path(args.file)
     
    # Load and plot
    channels, labels = extract_imu_to_csv(imu_file, imu_file.with_suffix('.csv'), num_samples=args.num)
    channels = [ [row[i] for row in channels] for i in range(8) ]
    plt.figure(figsize=(14, 12))
    for i in range(8):
        plt.subplot(4, 2, i+1)
        plt.plot(channels[i][1:], '-x')
        plt.title(labels[i])
        plt.xlabel("Sample Index")
        plt.ylabel("Value")
        plt.grid(True)
    plt.tight_layout()
    plt.show()



