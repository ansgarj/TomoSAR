import click
import compileall
import shutil
import re
from pathlib import Path

from ..binaries import check_required_binaries, run
from ..config import PACKAGE_PATH, PROJECT_PATH, SETTINGS_PATH, save_default

def warm_cache():
    """Pre-warm __pycache__ by compiling all modules."""

    compileall.compile_dir(PACKAGE_PATH, force=True, quiet=1)
    print(f"__pycache__ warmed for {PACKAGE_PATH}")

@click.command()
def setup() -> None:
    """Performs TomoSAR setup"""
    post_merge_path = PROJECT_PATH / ".git" / "hooks" / "post-merge"
    pre_push_path = PROJECT_PATH / ".git" / "hooks" / "pre-push"
    if not post_merge_path.exists():
        shutil.copy2(PROJECT_PATH / "setup" / "post-merge", post_merge_path)
        print("Project post-merge hook installed.")
    if not pre_push_path.exists():
        shutil.copy2(PROJECT_PATH / "setup" / "pre-push", pre_push_path)
        print("Project pre-push hook installed.")
    if not SETTINGS_PATH.exists():
        save_default()
        print("Default settings enabled (run tomosar settings to view)")
    run(["pip", "install", "-e", PROJECT_PATH])
    print("Installation updated.")
    check_required_binaries()
    warm_cache()

@click.command()
def dependencies() -> None:
    """Scan PATH for required binaries"""
    check_required_binaries()

@click.command()
def warmup() -> None:
    """Pre-warm __pycache__ by compiling all modules"""
    warm_cache()