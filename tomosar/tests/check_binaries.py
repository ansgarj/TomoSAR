import json

from tomosar.binaries import require_binary, load_dependencies

# Functions to check all dependencies
def check_required_binaries():
    deps = load_dependencies()
    missing = []
    for name, dep in deps.items():
        try:
            hint = json.dumps(dep, indent=4)
            require_binary(name, install_hint=hint)
        except RuntimeError as e:
            print(f"[Missing] {e}")
            missing.append(dep["Name"])
    if missing:
        print(f"{len(missing)} missing binaries: {missing}")
        return
    else:
        print("All required binaries are available.")
        _test_gnss()

def _test_gnss():
    pass