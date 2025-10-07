import shutil
import json
from importlib.resources import files
import subprocess

# Check if required binary is installed
def run(cmd: str | list):
    if not isinstance(cmd, list):
        cmd = [cmd]
    binary_name = cmd[0]
    require_binary(binary_name)  # Assuming this checks for binary availability
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}.\n"
            f"stdout:\n{e.stdout}\n"
            f"stderr:\n{e.stderr}"
        ) from e

def require_binary(name: str):
    try:
        dep = load_dependencies()[name]
    except:
        raise RuntimeError(f"Failed to find required binary '{name}' in tomosar.setup.dependencies.json")
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Required binary '{name}' not found in PATH.\n\033[1mSource\033[22m: {dep["Source"]}")
    return path

def load_dependencies() -> dict[str,dict]:
    path = files("tomosar.setup").joinpath("dependencies.json")
    with open(path) as f:
        return json.load(f)