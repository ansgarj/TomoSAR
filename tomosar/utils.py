# Imports
import os
import re
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import numpy as np
import pandas as pd
from skimage.measure import shannon_entropy
from scipy.special import polygamma
from scipy.stats import gamma
from scipy.linalg import svd
from scipy.optimize import least_squares
from scipy.ndimage import binary_closing
from sklearn.linear_model import RANSACRegressor, LinearRegression
import inspect
from datetime import timedelta, datetime, date, time
import math
from collections import defaultdict
from ftplib import FTP, error_perm
from getpass import getpass
from pathlib import Path
from importlib.resources import path as importpath
from contextlib import contextmanager
from typing import Iterator
import shutil
import gzip
import code
import sys

from .processing import circularize

# Custom warnings
def warn(message):
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    print(f"{filename}:{lineno}: {message}")

# Load interactive console
def interactive_console(var_dict: dict) -> None:
    pink = "\033[95m"
    reset = "\033[0m"
    bold = "\033[1m"
    bold_off = "\033[22m"

    sys.ps1 = f"{pink}>>> {reset}"
    sys.ps2 = f"{pink}... {reset}"

    print(f"{pink}{bold}Printing loaded variables ...{reset}")

    lines = [
        f"{pink}{bold}{name}:{bold_off} {value}{reset}"
        for name, value in var_dict.items()
    ]

    banner = "\n".join(lines)

    # Launch console with variables available
    code.interact(banner=banner, local=var_dict)

# Find change points in linear statistics
def find_inliers(signal, min_samples: int|float = 0.5, residual_threshold: float|None = None,
                 relative_threshold: float|None=0.2):
    n = len(signal)
    x = np.arange(n).reshape(-1,1)

    # Use RANSAC algorithm to estimate straight line
    ransac = RANSACRegressor(estimator=LinearRegression(), min_samples=min_samples,
                             residual_threshold=residual_threshold)
    ransac.fit(x, signal)
    predictions = ransac.predict(x)
   
    if relative_threshold:
        # Calculate inliers from relative threshold
        residuals = np.abs(signal - predictions)
        relative_residuals = residuals / np.abs(signal)
        inlier_mask = relative_residuals < relative_threshold
    else:
        # Get inliers from the RANSAC algorithm
        inlier_mask = ransac.inlier_mask_

    # Close small gaps
    inlier_mask = binary_closing(inlier_mask, structure=np.ones(3))

    return np.where(inlier_mask)[0]

# Statistics
def apply_variable_descriptions(df: pd.DataFrame):
    df.attrs["VariableUnits"] = {
        "height": "m",
        "mean_backscatter": "dB",
        "SD": "dB",
        "contrast": "dB"
    }

    df.attrs["VariableDescriptions"] = {
        "mean_backscatter": "Mean logarithmic backscatter.",
        "SD": "Standard deviation of logarithmic backscatter.",
        "contrast": "Logarithmic backscatter contrast.",
        "E": "Entropy of intensity image."
    }

    if 'mean_phase' in df.columns:
        df.attrs.setdefault("VariableUnits", {})["mean_phase"] = "n/a"
        df.attrs.setdefault("VariableDescriptions", {})["mean_phase"] = "Mean phase of raw tomogram."

    if 'SD_phase' in df.columns:
        df.attrs.setdefault("VariableUnits", {})["SD_phase"] = "n/a"
        df.attrs.setdefault("VariableDescriptions", {})["SD_phase"] = "Standard deviation of phase of raw tomogram."
    
    if 'RR' in df.columns:
        df.attrs.setdefault("VariableUnits", {})["RR"] = "n/a"
        df.attrs.setdefault("VariableDescriptions", {})["RR"] = "Estimated radiometric resolution."

    if 'cFactor' in df.columns:
        df.attrs.setdefault("VariableUnits", {})["cFactor"] = "n/a"
        df.attrs.setdefault("VariableDescriptions", {})["cFactor"] = "Estimated spatial speckle correlation factor."

def collect_statistics(tomogram: np.ndarray, height: np.ndarray, circ: bool = True) -> pd.DataFrame:
    # Circularize
    if circ:
        tomogram = circularize(tomogram)

    # Convert to intensity
    if np.isrealobj(tomogram):
        clx = False
        tomogram = 10 ** (tomogram / 10)
    else:
        clx = True
        phase = np.angle(tomogram)
        tomogram = np.abs(tomogram) ** 2


    N = tomogram.shape[0]
    mean_backscatter = []
    SD = []
    contrast = []
    E = []
    if clx:
        mean_phase = []
        SD_phase = []

    for n in range(N):
        slice_ = tomogram[n, ...]
        mean_val = np.nanmean(slice_)
        std_val = np.nanstd(slice_)
        max_val = np.nanmax(slice_)
        min_val = np.nanmin(slice_)
        entropy_val = shannon_entropy(slice_.astype(np.float64)) / 8

        mean_backscatter.append(10 * np.log10(mean_val))
        SD.append(10 * np.log10(std_val))
        contrast.append(10 * np.log10(max_val) - 10 * np.log10(min_val))
        E.append(entropy_val)

        if clx:
            slice_ = phase[n, :,:]
            mean_val = np.nanmean(slice_)
            std_val = np.nanstd(slice_)
            mean_phase.append(mean_val)
            SD_phase.append(std_val)

    df = pd.DataFrame({
        "height": height,
        "mean_backscatter": mean_backscatter,
        "SD": SD,
        "contrast": contrast,
        "E": E
    })

    if clx:
        df["mean_phase"] = mean_phase
        df["SD_phase"] = SD_phase

    apply_variable_descriptions(df)

    return df

# RR estimation
def estimaterr(tomogram, NNL=1, ds=1, tolerance=1E-2, npar=os.cpu_count()):
    if isinstance(ds, (list, tuple, np.ndarray)) and any(np.array(ds) > 1):
        tomogram = tomogram[::ds[0], ::ds[1], :]
    elif isinstance(ds, int) and ds > 1:
        tomogram = tomogram[::ds, ::ds, :]

    N = tomogram.shape[2]
    RR = np.zeros(N)
    cFactor = tolerance + np.ones(N)

    sz = tomogram.shape[:2]
    if sz[0] != sz[1]:
        min_sz = min(sz)
        tomogram = tomogram[:min_sz, :min_sz, :]

    for n in tqdm(range(N), desc="Estimating RR: ", leave=False):
        while cFactor[n] > tolerance:
            RR[n], cFactor[n] = _estimaterr_slice(tomogram[:, :, n], npar, NNL, tolerance=tolerance)

    return RR, cFactor

def _estimaterr_slice(I, npar, X0=None, ds=1, tolerance=1E-2):

    # Noise model function
    def noise_fun(x, xdata):
        return x[1] * np.sqrt(x[0] + xdata) + x[2]

    # Subsampling function
    def subsample(I, ds):
        return I[::ds, ::ds]
    
    if X0 is None:
        X0 = [polygamma(1, 1), 10, 0.1]

    if isinstance(X0, (int, float)):
        L0 = X0
        X0 = [polygamma(1, L0), 10, 0.1]
    else:
        L0 = 1 / (X0[0] + 5/3 - np.pi**2/6) + 0.5

    L1 = np.linspace(L0 + 2, L0, 500)
    L2 = np.linspace(L0, L0 / 2, 500)
    L = np.concatenate((L1, L2))
    N = len(L1)
    VAR1 = polygamma(1, L1)
    VAR2 = polygamma(1, L2)
    VAR = np.concatenate((VAR1, VAR2))

    J0 = subsample(I, ds) if ds > 1 else I
    l = min(512, min(J0.shape))
    J0 = J0[:l, :l]
    M = int(3 * l / 4)

    def process_noise(i):
        L_i = L[i]
        g_i = gamma.rvs(L_i, scale=1/L_i, size=J0.shape)
        J = 10 * np.log10(g_i * J0)
        S = svd(J, compute_uv=False)
        return np.mean(S[-M:])

    with ThreadPoolExecutor(max_workers=npar) as executor:
        P = list(executor.map(process_noise, range(len(L))))

    P = np.array(P)
    P1 = P[:N]
    P2 = P[N:]

    lower_bound = [0, 0, 0]
    upper_bound = [100, 100, 100]

    X1 = least_squares(lambda x: noise_fun(x, VAR1) - P1, X0, bounds=(lower_bound, upper_bound)).x
    X2 = least_squares(lambda x: noise_fun(x, VAR2) - P2, X0, bounds=(lower_bound, upper_bound)).x
    cFactor = abs(np.arctan(X1[1]) - np.arctan(X2[1]))

    if cFactor >= tolerance:
        if min(I.shape) / (ds + 1) < 512:
            return X0[0], cFactor
        X = least_squares(lambda x: noise_fun(x, VAR) - P, X2, bounds=(lower_bound, upper_bound)).x
        return _estimaterr_slice(I, npar, X, ds + 1, tolerance)
    else:
        X = least_squares(lambda x: noise_fun(x, VAR) - P, X2, bounds=(lower_bound, upper_bound)).x
        return X[0], cFactor

# Helper function to format duration from seconds to 'dd:hh:mm:ss' or 'hh:mm:ss'
def format_duration(seconds: int|float|timedelta, print_days: bool = False) -> str :
    if isinstance(seconds, (int, float)):
        duration = timedelta(seconds=seconds)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if print_days:
        return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Helper function to convert 'dd:hh:mm:ss' or 'hh:mm:ss' to seconds
def duration_seconds(duration: str) -> int:
    match = re.search(r'(\d{2}):(\d{2}):(\d{2})(?::(\d{2}))?')
    num_matched = sum(1 for g in match.groups() if g is not None)
    t = 0
    if num_matched == 3:
        t += int(match.group(1)) * 3600
        t += int(match.group(2)) * 60
        t += int(match.group(3))
    if num_matched == 4:
        t += int(match.group(1)) * 3600 * 24
        t += int(match.group(2)) * 3600
        t += int(match.group(3)) * 60
        t += int(match.group(4))
    return t

# Helper function to parse a string to datetime, date or time object
def parse_datetime_string(s: str) -> datetime|date|time:
    s = s.strip()
    
    datetime_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ]
    
    time_formats = [
        "%H:%M:%S",
        "%H:%M",
    ]
    
    for fmt in datetime_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    
    for fmt in date_formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    
    for fmt in time_formats:
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse '{s}' as datetime, date, or time.")

# Bin variables from a dict or pd.DataFrame according to the corresponding angular value
def bin_by_angle(theta, vars, bin_count=None, units='degrees', rotate: bool = False) -> tuple[dict[np.ndarray],str]:
    """
    Bins unwrapped angles into wrapped bins and computes the median of associated variables.

    Parameters:
        theta (array-like or str): Unwrapped angles (in degrees by default), or name of field in `vars`.
        vars (dict or pd.DataFrame): Dictionary or DataFrame of variables to bin.
        bin_count (int, optional): Number of bins over [0, 360). If None, estimated from gradient.
        units (str): 'degrees' or 'radians', the unit of theta

    Returns:
        tuple with (dict of np.array (2D) with binned medians for each variable and wrapping, name of angle key)
    """
    if isinstance(theta, str):
        theta_name = theta
        theta = vars[theta_name]
        angle_is_field = True
    else:
        angle_is_field = False

    theta = np.asarray(theta)

    if units == 'radians':
        theta = np.degrees(theta)

    if bin_count is None:
        bin_count = int(np.floor(360 / np.max(np.gradient(theta))))

    theta_wrapped = np.mod(theta, 360)

    wrap_index = np.round((theta - theta_wrapped) / 360).astype(int)
    unique_wraps, wrap_map = np.unique(wrap_index, return_inverse=True)
    wrap_count = len(unique_wraps)

    bin_edges = np.linspace(0, 360, bin_count + 1)
    bin_idx = np.digitize(theta_wrapped, bin_edges) - 1
    bin_idx[bin_idx == bin_count] = bin_count - 1

    var_names = vars.columns if isinstance(vars, pd.DataFrame) else vars.keys()
    binned = {name: [[] for _ in range(wrap_count)] for name in var_names}
    for i in range(len(theta)):
        b = bin_idx[i]
        if b < 0 or b >= bin_count:
            continue
        w = wrap_map[i]
        for name in var_names:
            value = vars[name].iloc[i] if isinstance(vars, pd.DataFrame) else vars[name][i]
            binned[name][w].append((b, value))

    result = {}
    for name in var_names:
        mat = np.full((bin_count, wrap_count), np.nan)
        for w in range(wrap_count):
            bin_values = [[] for _ in range(bin_count)]
            for b, val in binned[name][w]:
                bin_values[b].append(val)
            for b in range(bin_count):
                if bin_values[b]:
                    mat[b, w] = np.median(bin_values[b])
        result[name] = mat

    if angle_is_field:
        result[theta_name] = np.nanmedian(np.mod(result[theta_name], 360), axis=1)
        if units == 'radians':
            result[theta_name] = np.radians(result[theta_name])
    else:
        result['theta'] = (bin_edges[:-1] + bin_edges[1:]) / 2
        theta_name = 'theta'
    if rotate:
        _rotate_bins(result, theta_name)

    return result, theta_name

def _rotate_bins(binned_matrices, theta_name):
    """
    This functions rotates the output of abin so that the first row contains the start of the first
    wrapping, and counts angles from this position instead.
    """

    # Get the angle vector
    theta = binned_matrices[theta_name]  # shape: (bin_count,)

    # Get all matrices
    matrices = [binned_matrices[k] for k in binned_matrices if k != theta_name]

    # Find the first bin index where all matrices have non-NaN in the first wrapping column
    valid_mask = np.all([~np.isnan(mat[:, 0]) for mat in matrices], axis=0)
    first_valid_bin = np.argmax(valid_mask)
    start_theta = theta[first_valid_bin]

    for key in binned_matrices:
        binned_matrices[key] = np.roll(binned_matrices[key], -first_valid_bin, axis=0)
    
    binned_matrices[theta_name] = np.mod(binned_matrices[theta_name] - start_theta, 360)

    return binned_matrices

# Compute and handle stats from a dictionary with 1D np.ndarrays or pd.DataFrames with nesting
def compute_stats(d: dict):
    result_mean = {}
    result_std = {}
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively compute stats for nested dict
            mean_sub, std_sub = compute_stats(value)
            result_mean[key] = mean_sub
            result_std[key] = std_sub
        elif isinstance(value, np.ndarray):
            # Compute mean and stdiance for 1D array
            if len(value.shape) > 1:
                raise TypeError(f"Key {key} shape: {value.shape}")
            result_mean[key] = value.mean()
            result_std[key] = value.std()
        elif isinstance(value, pd.Series):
            result_mean[key] = value.mean()
            result_std[key] = value.std()
        elif isinstance(value, pd.DataFrame):
            df = value.iloc[:,1:]
            result_mean[key] = df.mean().to_dict()
            result_std[key] = df.std().to_dict()
        else:
            raise TypeError(f"Unsupported type for key '{key}': {type(value)}")
    return result_mean, result_std

def round_to_sig_digits(value, digits=3):
    if not isinstance(value, (float, np.floating)):
        raise TypeError(f"Value: {value} of type {type(value)}")
    if value == 0:
        return 0
    return round(value, -int(math.floor(math.log10(abs(value))) - (digits - 1)))

def round_to_same_decimal(value, reference):
    if reference == 0:
        return value
    if abs(reference) > abs(value):
        return round_to_sig_digits(value, 1)
    decimal_pos = -int(math.floor(math.log10(abs(reference))))
    return round(value, decimal_pos)

def combine_stats(means: dict, stds: dict, sig_digits=3) -> dict:
    combined = {}
    for key in means:
        mean_val = means[key]
        std_val = stds.get(key)

        if isinstance(mean_val, dict) and isinstance(std_val, dict):
            combined[key] = {}
            for subkey in mean_val:
                raw_std = std_val.get(subkey, 0)
                if not isinstance(raw_std, (float, np.floating)):
                    raise TypeError(f"{key}: {subkey}: {raw_std} of type {type(raw_std)}")
                std_dev = round_to_sig_digits(raw_std, sig_digits)
                rounded_mean = round_to_same_decimal(mean_val[subkey], std_dev)
                
                combined[key][subkey] = {
                    'mean': rounded_mean,
                    'std_dev': std_dev
                }
        else:
            raw_std = std_val or 0
            std_dev = round_to_sig_digits(raw_std, sig_digits)
            rounded_mean = round_to_same_decimal(mean_val, std_dev)

            combined[key] = {
                'mean': rounded_mean,
                'std_dev': std_dev
            }
    return combined

# Compute normalized RMSE between signal and ideal (symmetric):
# Relative root mean size of energy difference and mean energy (stable replacement for relative RMSE with values bounded in [0,sqrt(2)])
def normalized_rmse(signal: list[float]|np.ndarray, ideal: list[float]|np.ndarray) -> np.floating:
    if isinstance(signal, np.ndarray) and len(signal.shape) > 1:
        raise ValueError("Signal input is not a 1D array.")
    if isinstance(ideal, np.ndarray) and len(ideal.shape) > 1:
        raise ValueError("Ideal input is not a 1D array.")
    if len(signal) != len(ideal):
        raise ValueError("Signal and ideal do not match.")
    denominator = signal**2 + ideal**2
    numerator = 2 * (signal - ideal)**2
    relative_square_errors = np.zeros_like(denominator)
    nonzero_mask = denominator != 0
    relative_square_errors[nonzero_mask] = numerator[nonzero_mask] / denominator[nonzero_mask]

    return math.sqrt(relative_square_errors.mean())

# Add meta data at the beginning of a dict
def add_meta(data: dict, info_str: str, key: str = '__meta__') -> dict:
    if key in data and isinstance(data[key], str):
        new_data = data.copy()
        new_data[key] = data[key] + info_str
    elif key in data: 
        raise ValueError(f"Key {key} already exists and does not contain a string.")
    else:
        new_data = {key: info_str}
        new_data.update(data)
    return new_data

# Update nested dicts, merging pd.DataFrames by stacking columns when possible:
def update_nested_dict(original: dict, updates: dict) -> dict:
    for key, subdict in updates.items():
        if key in original and isinstance(original[key], dict) and isinstance(subdict, dict):
            update_nested_dict(original[key], subdict)
        elif key in original and isinstance(original[key], pd.DataFrame) and isinstance(subdict, pd.DataFrame):
            df1 = original[key]
            df2 = subdict
            if len(df1) != len(df2):
                original[key] = df2 # Overwrite mismatching DataFrames
            df2 = df2.set_index(df1.index) # Align indices if needed
            overlapping = df1.columns.intersection(df2.columns)
            df1_clean = df1.drop(columns=overlapping) # Overwrite columns in original
            original[key] = pd.concat([df1_clean, df2], axis=1) # Concatenate 
        else:
            original[key] = subdict  # Add new key or overwrite non-dict
    return original

def invert_nested_dict(nested):
    # Get all outer keys
    outer_keys = set(nested.keys())

    # Invert the dictionary
    inverted = defaultdict(dict)
    for outer_key, inner_dict in nested.items():
        for inner_key, value in inner_dict.items():
            inverted[inner_key][outer_key] = value

    # Sort keys: complete ones first, incomplete ones last
    sorted_keys = sorted(
        inverted.keys(),
        key=lambda k: len(inverted[k]) < len(outer_keys)  # False < True → complete first
    )

    # Reconstruct sorted dict
    return {k: inverted[k] for k in sorted_keys}

# Function to return a string representation of the model resulting from a LinearRegression().fit()
def linear_model_str(model: LinearRegression, var: str = 't', rounded: bool = True) -> str:
    if model.coef_[0] == 0 and model.intercept_ == 0:
        return "0"
    if rounded:
        return f"{f'{model.intercept_:.3g}' if model.intercept_ != 0 else ''}{
                    f' + {model.coef_[0]:.3g} * {var}' if model.coef_[0] > 0 else  \
                    f' - {abs(model.coef_[0]):.3g} * {var}' if model.coef_[0] < 0 else \
                    ''
                }"
    else:
        return f"{f'{model.intercept_}' if model.intercept_ != 0 else ''}{
                    f' + {model.coef_[0]} * {var}' if model.coef_[0] > 0 else  \
                    f' - {abs(model.coef_[0])} * {var}' if model.coef_[0] < 0 else \
                    ''
                }"

def prompt_ftp_login(server: str, max_attempts: int = 3, default_user: str = "", anonymous: bool = False):
    """
    Prompts for FTP login credentials and retries if login fails.
    Returns a connected FTP object.
    """
    user_prompt = f"Enter username for {server}" + f"{f' (press enter for {default_user})' if default_user else ''}" + ": "
    for attempt in range(1, max_attempts + 1):
        if anonymous:
            ftp_user = "anonymous"
            ftp_pass = "none"
        else:
            ftp_user = input(user_prompt)
            if not ftp_user:
                ftp_user = default_user

            ftp_pass = getpass("Enter password: ")
            
        try:
            ftp = FTP(server)
            ftp.login(user=ftp_user, passwd=ftp_pass)
            print(f"Login successful ({server}).")
            return ftp, ftp_user, ftp_pass
        except error_perm as e:
            print(f"Login failed ({attempt}/{max_attempts}): {e}")
            if attempt == max_attempts:
                raise ConnectionError("Maximum login attempts exceeded.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

def gunzip(input_path: Path|str, output_path: Path|str = None) -> Path:
    input_path = Path(input_path)
    if input_path.suffix != '.gz':
        raise ValueError(f"{input_path} is not a .gz file")

    if not output_path:
        output_path = input_path.with_suffix('')  # Strip .gz
    with gzip.open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())

    input_path.unlink()  # Delete the original .gz file
    return output_path

@contextmanager
def data_path(path: str | Path | None, filename: str) -> Iterator[Path]:
    if path:
        path = Path(path)
        if path.exists() and path.is_file():
            yield path
            return

    with importpath('tomosar.data', filename) as resource_path:
        resource_path = Path(resource_path)
        if resource_path.exists() and resource_path.is_file():
            # Create a temp file in the current working directory
            tmp_path = Path(os.getcwd()) / filename
            tmp_path = tmp_path.with_suffix(".tmp")
            shutil.copy(resource_path, tmp_path)
            try:
                yield tmp_path
            finally:
                tmp_path.unlink(missing_ok=True)  # Clean up after use
            return

    raise FileNotFoundError(
        f"{f"The file {path} was not found, and " if path else ""}'{filename}' is not a valid tomosar.data file."
    )
