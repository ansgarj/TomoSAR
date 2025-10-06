#!/usr/bin/env python3

import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import subprocess
import json

def read_pos_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip header lines
    data_lines = [line for line in lines if not line.startswith('%')]

    # Parse numeric data
    try:
        data = [list(map(float, line.split())) for line in data_lines]
        data = np.array(data)
    except ValueError:
        raise ValueError(f"Could not parse numeric data from {filepath}")
    

    # Auto-detect coordinate columns (assumes columns 3–5 are E/N/U or X/Y/Z)
    if data.shape[1] >= 5:
        coords = data[:, 2:5]
        gpst = data[:, 1]
        q = data[:, 5]
        q = np.sum(q == 1) / len(q) * 100
    else:
        raise ValueError(f"Unexpected format in {filepath}: not enough columns")
    
    return coords, q, gpst


def plot_coordinates(coords1, coords2, labels, title1, title2):
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    for i in range(3):
        axes[i].plot(coords1[:, i], label=title1, alpha=0.7)
        axes[i].plot(coords2[:, i], label=title2, alpha=0.7)
        axes[i].set_ylabel(labels[i])
        axes[i].legend()
        axes[i].grid(True)

    axes[-1].set_xlabel('Epoch Index')
    plt.tight_layout()
    plt.show()

def plot_difference(t1, coords1, t2, coords2, labels):
    common_times = np.intersect1d(t1, t2)

    # Get indices in t1 and t2 where these common times occur
    indices_t1 = np.nonzero(np.isin(t1, common_times))[0]
    indices_t2 = np.nonzero(np.isin(t2, common_times))[0]
    diff = coords1[indices_t1] - coords2[indices_t2]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for i in range(3):
        axes[i].plot(diff[:, i], color='purple', label=f'Difference ({labels[i]})')
        axes[i].set_ylabel(f'Δ {labels[i]}')
        axes[i].legend()
        axes[i].grid(True)
    axes[-1].set_xlabel('Epoch Index')
    diff_mean = diff.mean(axis=0)
    diff_std = diff.std(axis=0)
    print(f"Mean difference: X={diff_mean[0]:.2g} m ({diff_std[0]:.2g} m), Y={diff_mean[1]:.2g} m ({diff_std[1]:.2g} m), Z={diff_mean[2]:.2g} m ({diff_std[2]:.2g} m)")
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Compare .pos files from two rnx2rtkp calls ")
    parser.add_argument("rover_obs", help="Path to rover OBS file")
    parser.add_argument("base1_obs", help="Path to first base OBS file")
    parser.add_argument("base2_obs", help="Path to second base OBS file")
    parser.add_argument("nav", help="Path to NAV file")
    parser.add_argument("-k", "--config", help="Path to config file", default=None)
    parser.add_argument("-s", "--sbas", help="Path to SBAS corrections file", default=None)
    parser.add_argument("-m", "--mocoref", help="Path to mocoref.json file for first base", default=None)
    parser.add_argument("-f", "--force", action="store_true", help="Force reprocessing")
    args = parser.parse_args()

    rover_obs = Path(args.rover_obs)
    base1_obs = Path(args.base1_obs)
    base2_obs = Path(args.base2_obs)
    nav_path = Path(args.nav)
    if args.sbas:
        sbs_path = Path(args.sbas)
    if args.config:
        conf_path = Path(args.config)
    if args.mocoref:
        mocoref_path = Path(args.mocoref)

    pos1_path =  base1_obs.with_suffix(".pos")
    pos2_path = base2_obs.with_suffix(".pos")
    # Base 1 command
    cmd = [
        'rnx2rtkp',
          "-o", pos1_path,
    ]
    # Add config file if available
    if args.config:
        cmd.extend(['-k', conf_path])
    # Add reference position from mocoref if available
    if args.mocoref:
        with open(mocoref_path, 'r') as f:
            mocoref = json.load(f)
        print(f"mocoref: {mocoref}")
        h = mocoref["h"] - 0.2
        cmd.extend(["-l", str(mocoref["lat"]), str(mocoref["lon"]), str(h)])
    # Add rinex files
    cmd.extend([rover_obs, base1_obs, nav_path])
    # Add sbs file of available
    if args.sbas:
        cmd.append(sbs_path)
    if not pos1_path.exists() or args.force:
        print(f"{base1_obs} SPP ...")
        print(*cmd)
        subprocess.run(cmd)
    # Read results
    coords1, q1, t1 = read_pos_file(pos1_path)
    # Display Q=1 percentage
    print(f"{pos1_path} Q1: {q1} %")

    # Base 2 command 
    cmd = [
        'rnx2rtkp',
          "-o", pos2_path,
    ]
    # Add config file if available
    if args.config:
        cmd.extend(['-k', conf_path])
    # Add rinex files
    cmd.extend([rover_obs, base2_obs, nav_path])
    # Add sbs file of available
    if args.sbas:
        cmd.append(sbs_path)
    # Process second base
    if not pos2_path.exists() or args.force:
        print(f"{base2_obs} SPP ...")
        subprocess.run(cmd)

    # Read results
    coords2, q2, t2 = read_pos_file(pos2_path)
    # Display Q=1 percentage
    print(f"{pos2_path} Q1: {q2} %")

    labels = ['East/X', 'North/Y', 'Up/Z']


    #plot_coordinates(coords1, coords2, labels, pos1, pos2)

    plot_difference(t1, coords1, t2, coords2, labels)

if __name__ == "__main__":
    main()
