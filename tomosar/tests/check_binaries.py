import json
from importlib.resources import files

from tomosar.utils import require_binary

# Functions to check all dependencies
def load_dependencies():
    path = files("tomosar.config").joinpath("dependencies.json")
    with open(path) as f:
        return json.load(f)

def check_required_binaries():
    deps = load_dependencies()
    missing = []
    for dep in deps:
        try:
            hint = json.dumps(dep, indent=4)
            require_binary(dep["Name"], install_hint=hint)
        except RuntimeError as e:
            print(f"[Missing] {e}")
            missing.append(dep["Name"])
    if missing:
        print(f"{len(missing)} missing binaries: {missing}")
    else:
        print("All required binaries are available.")