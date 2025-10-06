#!/usr/bin/env python3

import os
import time as Time
import code
import click
from datetime import datetime
from pathlib import Path

from tomosar import ImageInfo, TomoScenes
from tomosar.forging import tomoforge as run_tomoforge

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--single", is_flag=True, help="Process 1-look data in interferometric bands.")
@click.option("--nopair", is_flag=True, help="Avoid processing 2-look data in interferometric bands.")
@click.option("--RR", is_flag=True, help="Estimate RR and SSF in multilooked tomogram.")
@click.option("--fused", is_flag=True, help="Process only fused tomograms.")
@click.option("--sub", is_flag=True, help="Process only subsurface tomograms.")
@click.option("--sup", is_flag=True, help="Process only supersurface tomograms.")
@click.option("--canopy", is_flag=True, help="Process only canopy tomograms.")
@click.option("--phh", is_flag=True, help="Only process files from P-band.")
@click.option("--lxx", is_flag=True, help="Only process files from L-band.")
@click.option("--lhh", is_flag=True)
@click.option("--lvv", is_flag=True)
@click.option("--lhv", is_flag=True)
@click.option("--lvh", is_flag=True)
@click.option("--cvv", is_flag=True)
@click.option("--load", is_flag=True, help="Load generated tomogram scenes into an interactive Python console.")
@click.option("-o", "--out", type=click.Path(path_type=Path), default=".", help="Output directory.")
@click.option("-m", "--masks", type=str, default="", help="Folder containing shapefile masks.")
@click.option("-n", "--npar", type=int, default=os.cpu_count(), help="Number of parallel threads.")
@click.option("--folder", type=str, default=None)
@click.option("-d", "--date", type=str, default=None)
@click.option("-t", "--time", type=str, default=None)
@click.option("-s", "--spiral", type=int, default=None)
@click.option("-w", "--width", type=float, default=None)
@click.option("-r", "--res", type=float, default=None)
@click.option("-f", "--refr", type=float, default=None)
@click.option("--lat", type=float, default=None)
@click.option("--lon", type=float, default=None)
@click.option("--thresh", type=float, default=None)
@click.option("--smo", type=float, default=None)
@click.option("--ham", type=float, default=None)
@click.option("--squint", type=float, default=None)
@click.option("--text", type=str, default=None)
@click.option("--DC", type=float, default=None)
@click.option("--DL", type=float, default=None)
@click.option("--HC", type=float, default=None)
@click.option("--HV", type=float, default=None)
def tomoforge(paths, single, nopair, RR, fused, sub, sup, canopy,
         phh, lxx, lhh, lvv, lhv, lvh, cvv, load,
         out, masks, npar, folder, date, time, spiral, width, res, refr,
         lat, lon, thresh, smo, ham, squint, text, DC, DL, HC, HV) -> TomoScenes:

    time_start = Time.time()

    print("Input paths:", paths)
    print("Output directory:", out)
    print("Mask directory:", masks)
    print("Parallel threads:", npar)

    # Construct filter
    folder = os.path.abspath(folder) if folder else None
    date_obj = datetime.strptime(date, "%Y-%m-%d") if date else datetime.strptime("1900-01-01", "%Y-%m-%d")
    if time:
        timestamp = datetime.strptime(time, "%H:%M:%S")
        date_obj = date_obj.replace(hour=timestamp.hour, minute=timestamp.minute, second=timestamp.second)

    bands = []
    if phh: bands.append("phh")
    if lxx: bands.extend(["lhh", "lvv", "lhv", "lvh"])
    if lhh: bands.append("lhh")
    if lvv: bands.append("lvv")
    if lhv: bands.append("lhv")
    if lvh: bands.append("lvh")
    if cvv: bands.append("cvv")

    filter = ImageInfo(
        folder=folder, filename=None, date=date_obj, spiral=spiral, band=bands,
        width=width, res=res, smo=smo, ham=ham, refr=refr, lat=lat, lon=lon,
        hoff=None, depth=None, DC=DC, DL=DL, HC=HC, HV=HV, thresh=thresh,
        squint=squint, text=text
    )

    # Dispatch processing
    tomo_scenes = run_tomoforge(
        paths=paths, filter=filter, single=single, nopair=nopair, RR=RR,
        fused=fused, sub=sub, sup=sup, canopy=canopy,
        masks=masks, npar=npar, out=out
    )

    print(f"Processing completed in {Time.time() - time_start:.2f} seconds.")
    if load:
        code.interact(local=locals())

    return tomo_scenes