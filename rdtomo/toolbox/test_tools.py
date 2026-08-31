import click
import os
from datetime import timedelta
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt

from ..gnss import fetch_swepos, station_ppp as run_ppp, ppk as run_ppk, ubx2rnx
from ..manager import resource
from ..position import DeltaPos
from ..config import LOCAL, Settings
from ..data import DataDir

@click.group()
def test() -> None:
    """Entry point for tomotest utilities."""
    pass

@test.command()
@click.option("--savar", is_flag=True, help="Process Savar test file instead of default (SVB)")
def gnss(savar: bool = False) -> None:
    """Test GNSS processing capabilities."""
    test_dir = LOCAL / "gnss_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(test_dir)
    print(f"Running test in {test_dir} ...")
    if savar:
        test_file = "TEST_FILE_SAVAR"
    else:
        test_file = "TEST_FILE_SVB"
    with resource(None, test_file) as ubx:
        rover_obs, rover_nav, _ = ubx2rnx(ubx, sbs=False)
        if rover_obs.is_file() and rover_nav.is_file():
            print("TEST: Drone GNSS test sample succesfully converted to RINEX")
            print()
        else:
            raise RuntimeError("rtklib binary convbin failed to generate RINEX files from test UBX file.")
        
        print("Reading RINEX data ...", flush=True)
        swepos_obs, swepos_nav = fetch_swepos(rover_obs, fetch_nav=True, min_dur=4, output_dir="SWEPOS")
        if swepos_obs.is_file() and swepos_nav.is_file():
            print("TEST: Download, unpacking and merging sucessful")
        else:
            raise RuntimeError("Download, unpacking or merging of RINEX files from Swepos failed. See above.")

        print()
        base_pos, results = run_ppp(swepos_obs, swepos_nav, header=False, out_path=swepos_obs.with_suffix(".out"), retain=True, force_splice=True)
        sp3_file = results["sp3"] 
        clk_file = results["clk"]
    
        diff: DeltaPos = base_pos - results["header_position"]
        if diff.norm() < 0.01:
            print(f"Distance: {diff} (E: {diff.east[0]:.4f} m, N: {diff.north[0]:.4f} m, U: {diff.up[0]:.4f} m)")
            print("TEST: station PPP sucessfully achieved sub-centimetre accuracy")
            print()
        else:
            print(f"Distance: {diff} (E: {diff.east[0]:.4f} m, N: {diff.north[0]:.4f} m, U: {diff.up[0]:.4f} m)")
            raise RuntimeError("Station PPP processing produced poor solution")

        # Run PPK
        out_path = rover_obs.with_suffix(".pos")
        _, result = run_ppk(
            rover_obs=rover_obs,
            base_obs=swepos_obs,
            nav_file=rover_nav,
            out_path=out_path,
            sp3_file=sp3_file,
            clk_file=clk_file,
            precise=True
        )
        q = result["quality"]
        gpst = result["gpst"]
        try: 
            quality_conversion = np.sum(q == 1) / len(q) * 100
            dur = timedelta(seconds=(gpst[-1] - gpst[0]))
            print(f"Length of processed data: {dur}")
        except:
            raise RuntimeError("rnx2rtkp failed to produce a .pos file with valid content")

        if quality_conversion > 99 and dur == timedelta(minutes=10, seconds=1.6):
            print("TEST: PPK sucessful")
            print()
            print("GNSS processing OPERATIONAL!")
        else:
            raise RuntimeError("rnx2rtkp produced poor Q1 quality or lost time, check tomosar settings PPK_CONFIG")
        
@test.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=DataDir), default=None)
@click.option("--swepos", "use_swepos", is_flag=True, help="Substitute for base OBS with files from nearest Swepos station")
@click.option("-z", "-zip", "is_zip", is_flag=True, help="Force base OBS and mocoref.moco files to be generated from a Reach ZIP archive")
@click.option("--mocoref", "is_mocoref", is_flag=True, help="Force mocoref data to be read from mocoref.moco file")
@click.option("--csv", "is_csv", is_flag=True, help="Force mocoref data to be read from CSV file")
@click.option("--json", "is_json", is_flag=True, help="Force mocoref data to be read from JSON file")
@click.option("--llh", "is_llh", is_flag=True, help="Force mocoref data to be read from LLH file")
@click.option("--rnx", "is_rnx", is_flag=True, help="Force base OBS to be directly accessible (not extracted)")
@click.option("--hcn", "is_hcn", is_flag=True, help="Force base OBS to be extracted from a .HCN file")
@click.option("--rtcm3", "is_rtcm3", is_flag=True, help="Force base OBS to be extracted from a .RTCM3 file")
@click.option("-h", "--header", "use_header", is_flag=True, help="Read mocoref data from RINEX header")
@click.option("-a", "--atx", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the satellite antenna .atx file")
@click.option("-r", "--receiver", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the .atx file containing receiver antenna info")
@click.option("--downloads", type=int, default=10, help="Max number of parallel downloads (default: 10)")
@click.option("--attempts", type=int, default=3, help="Max number of attempts for each file (default: 3)")
@click.option("-m", "--mask", "elevation_mask", type=float, default=None, help="Elevation mask for satellites")
@click.option("-l", "--line", "csv_line", type=int, default=1, help="Line in CSV file to read data from (default=1)")
@click.option("--offset", type=float, default=-0.079, help="Specify vertical PCO between mocoref data log receiver and drone processing receiver (default=-0.079) for CSV files")
@click.option("--overlap", "minimal_overlap", type=float, default=10, help="Specify minimal overlap between base OBS and drone flight in minutes (default: 10 minutes)")
def station_ppp(
    path: DataDir|None,
    use_swepos: bool,
    is_zip: bool,
    is_mocoref: bool,
    is_csv: bool,
    is_json: bool,
    is_llh: bool,
    is_rnx: bool,
    is_hcn: bool,
    is_rtcm3: bool,
    use_header: bool,
    atx: Path,
    receiver: Path,
    downloads: int,
    attempts: int,
    elevation_mask: float,
    csv_line: int,
    offset: float,
    minimal_overlap: float
) -> None:
    """Test station PPP against ground truth as found in a mocoref file. This test opens a Data Directory to extract data and runs
    station PPP on the base OBS, and compares it against the mocoref position."""
    if not path:
        path = DataDir.cwd()

    with path.open(
        atx = atx,
        receiver = receiver,
        use_swepos = use_swepos,
        use_ppp = False,
        use_header=use_header,
        is_zip = is_zip,
        is_mocoref = is_mocoref,
        is_csv = is_csv,
        is_llh = is_llh,
        is_json = is_json,
        is_rnx = is_rnx,
        is_hcn = is_hcn,
        is_rtcm3 = is_rtcm3,
        csv_line = csv_line,
        offset = offset,
        download_attempts = attempts,
        max_downloads = downloads,
        elevation_mask = elevation_mask,
        minimal_overlap = minimal_overlap,
    ) as data:
        pos, _ = run_ppp(
            data.base_obs,
            navglo_path=data.base_nav,
            atx_path=atx,
            antrec_path=receiver,
            sp3_file=data.sp3,
            clk_file=data.clk,
            inx_file=data.inx,
            download_dir=data.container,
            max_downloads=downloads,
            max_retries=attempts,
            elevation_mask=elevation_mask,
            header=False,
            make_mocoref=False
        )
        diff = pos - data.base_pos

    distance = diff.norm()
    print(f"Distance: {distance:.2f} m (E: {diff[0]:.2f} m, N: {diff[1]:.2f} m, U: {diff[2]:.2f} m)")

@test.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=DataDir), default=None)
@click.option("--swepos", "use_swepos", is_flag=True, help="Substitute for base OBS with files from nearest Swepos station")
@click.option("--ppp", "use_ppp", is_flag=True, help="Subsitute for mocoref data by running static PPP on base OBS")
@click.option("-z", "-zip", "is_zip", is_flag=True, help="Force base OBS and mocoref.moco files to be generated from a Reach ZIP archive")
@click.option("--mocoref", "is_mocoref", is_flag=True, help="Force mocoref data to be read from mocoref.moco file")
@click.option("--csv", "is_csv", is_flag=True, help="Force mocoref data to be read from CSV file")
@click.option("--json", "is_json", is_flag=True, help="Force mocoref data to be read from JSON file")
@click.option("--llh", "is_llh", is_flag=True, help="Force mocoref data to be read from LLH file")
@click.option("--rnx", "is_rnx", is_flag=True, help="Force base OBS to be directly accessible (not extracted)")
@click.option("--hcn", "is_hcn", is_flag=True, help="Force base OBS to be extracted from a .HCN file")
@click.option("--rtcm3", "is_rtcm3", is_flag=True, help="Force base OBS to be extracted from a .RTCM3 file")
@click.option("-h", "--header", "use_header", is_flag=True, help="Read mocoref data from RINEX header (no separate file, use ONLY if RINEX header is known to contain precise position)")
@click.option("-a", "--atx", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the satellite antenna .atx file")
@click.option("-r", "--receiver", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the .atx file containing receiver antenna info")
@click.option("--downloads", type=int, default=10, help="Max number of parallel downloads (default: 10)")
@click.option("--attempts", type=int, default=3, help="Max number of attempts for each file (default: 3)")
@click.option("-m", "--mask", "elevation_mask", type=float, default=None, help="Elevation mask for satellites")
@click.option("-l", "--line", "csv_line", type=int, default=1, help="Line in CSV file to read data from (default=1)")
@click.option("--offset", type=float, default=-0.079, help="Specify vertical PCO between mocoref data log receiver and drone processing receiver (default=-0.079) for CSV files")
@click.option("--overlap", "minimal_overlap", type=float, default=10, help="Specify minimal overlap between base OBS and drone flight in minutes (default: 10 minutes)")
@click.option("-k", "--config", type=click.Path(exists=True, path_type=Path), default=None, help="Specify external config file for rnx2rtkp")
def precise_ppk(
    path: DataDir|None,
    use_swepos: bool,
    use_ppp: bool,
    is_zip: bool,
    is_mocoref: bool,
    is_csv: bool,
    is_json: bool,
    is_llh: bool,
    is_rnx: bool,
    is_hcn: bool,
    is_rtcm3: bool,
    use_header: bool,
    atx: Path,
    receiver: Path,
    downloads: int,
    attempts: int,
    elevation_mask: float,
    csv_line: int,
    offset: float,
    minimal_overlap: float,
    config: Path,
) -> None:
    """Compare solutions from precise and broadcast ephemeris data in PPK post processing. This test opens a Data Directory and runs PPK
    post processing on the drone once with precise mode and once with broadcast ephemeris data."""

    if not path:
        path = DataDir.cwd()

    with path.open(
        require_drone=True,
        atx = atx,
        receiver = receiver,
        use_swepos = use_swepos,
        use_ppp = use_ppp,
        use_header=use_header,
        is_zip = is_zip,
        is_mocoref = is_mocoref,
        is_csv = is_csv,
        is_llh = is_llh,
        is_json = is_json,
        is_rnx = is_rnx,
        is_hcn = is_hcn,
        is_rtcm3 = is_rtcm3,
        csv_line = csv_line,
        offset = offset,
        download_attempts = attempts,
        max_downloads = downloads,
        elevation_mask = elevation_mask,
        minimal_overlap = minimal_overlap,
    ) as data:
        if use_swepos and not elevation_mask:
            elevation_mask = 20 # Precise 
        coords_prec, results_prec = data.ppk(
            atx=atx,
            receiver=receiver,
            use_precise=True,
            config=config,
            elevation_mask=elevation_mask,
        )
        if use_swepos and not elevation_mask:
            elevation_mask = 5 # Broadcast
        coords_bc, results_bc = data.ppk(
            atx=atx,
            receiver=receiver,
            use_precise=False,
            config=config,
            elevation_mask=elevation_mask,
        )

    gpst, q_prec = results_prec["gpst"], results_prec["quality"]
    q_bc = results_bc["quality"]

    float_prec = ~(q_prec == 1)
    float_bc = ~(q_bc == 1)
    
    fig, axs = plt.subplots(3, 1, squeeze=False, figsize=(12, 12), sharex=True, tight_layout=True)
    axs = axs.flatten()
    ax = axs[0]
    ax.plot(gpst, coords_prec.h, 'g-', label=f"Precise track")
    ax.plot(gpst, coords_bc.h, 'b:', label=f"Broadcast track")
    ax.plot(gpst[float_prec], coords_prec.h[float_prec], 'g+', label=f"Precise float")
    ax.plot(gpst[float_bc], coords_bc.h[float_bc], 'b+', label=f"Broadcast float")
    ax.set_ylabel("Ellipsoidal Height (m)")
    ax.legend()

    ax = axs[1]
    diff = coords_bc - coords_prec
    ax.plot(gpst, diff.norm(horizontal=True), label="Horizontal")
    ax.plot(gpst, diff.norm(vertical=True), label="Vertical")
    ax.set_ylabel("Distance (m)")
    ax.legend()

    ax = axs[2]
    ax.plot(gpst, results_prec["ratio"], 'r-', label="Precise")
    ax.plot(gpst, results_bc["ratio"], 'b-', label="Broadcast")
    ax.set_ylabel("AR Ratio")
    ax.legend()

    fig.supxlabel("GPST (s)")

    plt.show()

@test.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=DataDir), default=None)
@click.option("--swepos", "use_swepos", is_flag=True, help="Substitute for base OBS with files from nearest Swepos station")
@click.option("--ppp", "use_ppp", is_flag=True, help="Subsitute for mocoref data by running static PPP on base OBS")
@click.option("-z", "-zip", "is_zip", is_flag=True, help="Force base OBS and mocoref.moco files to be generated from a Reach ZIP archive")
@click.option("--mocoref", "is_mocoref", is_flag=True, help="Force mocoref data to be read from mocoref.moco file")
@click.option("--csv", "is_csv", is_flag=True, help="Force mocoref data to be read from CSV file")
@click.option("--json", "is_json", is_flag=True, help="Force mocoref data to be read from JSON file")
@click.option("--llh", "is_llh", is_flag=True, help="Force mocoref data to be read from LLH file")
@click.option("--rnx", "is_rnx", is_flag=True, help="Force base OBS to be directly accessible (not extracted)")
@click.option("--hcn", "is_hcn", is_flag=True, help="Force base OBS to be extracted from a .HCN file")
@click.option("--rtcm3", "is_rtcm3", is_flag=True, help="Force base OBS to be extracted from a .RTCM3 file")
@click.option("-h", "--header", "use_header", is_flag=True, help="Read mocoref data from RINEX header (no separate file, use ONLY if RINEX header is known to contain precise position)")
@click.option("--broadcast", "use_broadcast", is_flag=True, help="Use broadcast ephemeris data")
@click.option("-a", "--atx", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the satellite antenna .atx file")
@click.option("-r", "--receiver", type=click.Path(exists=True, path_type=Path), default=None, help="Path to the .atx file containing receiver antenna info")
@click.option("--downloads", type=int, default=10, help="Max number of parallel downloads (default: 10)")
@click.option("--attempts", type=int, default=3, help="Max number of attempts for each file (default: 3)")
@click.option("-m", "--mask", "elevation_mask", type=float, default=None, help="Elevation mask for satellites")
@click.option("-l", "--line", "csv_line", type=int, default=1, help="Line in CSV file to read data from (default=1)")
@click.option("--offset", type=float, default=-0.079, help="Specify vertical PCO between mocoref data log receiver and drone processing receiver (default=-0.079) for CSV files")
@click.option("--overlap", "minimal_overlap", type=float, default=10, help="Specify minimal overlap between base OBS and drone flight in minutes (default: 10 minutes)")
@click.option("-k", "--config", type=click.Path(exists=True, path_type=Path), default=None, help="Specify external config file for rnx2rtkp")
def ppk(
    path: DataDir|None,
    use_swepos: bool,
    use_ppp: bool,
    is_zip: bool,
    is_mocoref: bool,
    is_csv: bool,
    is_json: bool,
    is_llh: bool,
    is_rnx: bool,
    is_hcn: bool,
    is_rtcm3: bool,
    use_header: bool,
    use_broadcast: bool,
    atx: Path,
    receiver: Path,
    downloads: int,
    attempts: int,
    elevation_mask: float,
    csv_line: int,
    offset: float,
    minimal_overlap: float,
    config: Path,
) -> None:
    """Compare solutions from internal and raw PPK processing. This test opens a Data Directory and runs PPK processing
    on the drone once with the internal resources, and once raw (including no files downloaded)."""

    if not path:
        path = DataDir.cwd()

    with path.open(
        require_drone=True,
        atx = atx,
        receiver = receiver,
        use_swepos = use_swepos,
        use_ppp = use_ppp,
        use_header=use_header,
        is_zip = is_zip,
        is_mocoref = is_mocoref,
        is_csv = is_csv,
        is_llh = is_llh,
        is_json = is_json,
        is_rnx = is_rnx,
        is_hcn = is_hcn,
        is_rtcm3 = is_rtcm3,
        csv_line = csv_line,
        offset = offset,
        download_attempts = attempts,
        max_downloads = downloads,
        elevation_mask = elevation_mask,
        minimal_overlap = minimal_overlap,
    ) as data:
        if use_swepos and not elevation_mask:
            if not use_broadcast:
                elevation_mask = 20 # Precise 
            else:
                elevation_mask = 5
        coords_int, results_int = data.ppk(
            atx=atx,
            receiver=receiver,
            use_precise=not use_broadcast,
            config=config,
            elevation_mask=elevation_mask,
        )
        coords_raw, results_raw = data.ppk(
            use_precise=False,
            config=config,
            elevation_mask=elevation_mask,
            raw=True
        )
    
    gpst, q_int = results_int["gpst"], results_int["quality"]
    q_raw = results_raw["quality"]

    # Index tracking
    int_only = (q_int != 1) & (q_raw == 1)
    raw_only = (q_raw != 1) & (q_int == 1)
    both = (q_int != 1) & (q_raw != 1)
    
    fig, axs = plt.subplots(3, 1, squeeze=False, figsize=(12, 12), sharex=True, tight_layout=True)
    axs = axs.flatten()
    ax = axs[0]
    ax.plot(gpst, coords_int.h, 'g-', label="Internal track")
    ax.plot(gpst, coords_raw.h, 'b:', label="Raw track")
    ax.plot(gpst[int_only], coords_int.h[int_only], 'r+', label=f"Internal only float")
    ax.plot(gpst[raw_only], coords_raw.h[raw_only], 'm+', label=f"Raw only float")
    ax.plot(gpst[both], coords_int.h[both], 'y+', label=f"Both float (internal)")
    ax.plot(gpst[both], coords_raw.h[both], 'c+', label=f"Both float (raw)")
    ax.set_ylabel("Ellipsoidal Height (m)")
    ax.legend()
    
    ax = axs[1]
    diff = coords_raw - coords_int 
    ax.plot(gpst, diff.norm(horizontal=True), label="Horizontal")
    ax.plot(gpst, diff.norm(vertical=True), label="Vertical")
    ax.set_ylabel("Distance (m)")
    ax.legend()

    ax = axs[2]
    ax.plot(gpst, results_int["ratio"], 'g-', label="Internal")
    ax.plot(gpst, results_raw["ratio"], 'r-', label="Raw")
    ax.set_ylabel("AR Ratio")
    ax.legend()

    fig.supxlabel("GPST (s)")

    plt.show()
