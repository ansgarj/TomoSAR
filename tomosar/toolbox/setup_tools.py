import click
import compileall
import tomosar
import os
import shutil
from pathlib import Path

from tomosar.utils import warn
from tomosar.binaries import check_required_binaries, run

PACKAGE_PATH = os.path.dirname(tomosar.__file__)
PROJECT_PATH = Path(tomosar.__file__).parent.parent

def pyproject_changed() -> bool:
    """Checks whether pyproject.toml was changed in the last merge (pull)"""
    try:
        # Run the git diff-tree command
        result =run(["git", "diff-tree", "-r", "--name-only", "--no-commit-id", "ORIG_HEAD", "HEAD"])
        
        # Check if pyproject.toml is in the output
        changed_files = result.stdout.splitlines()
        return "pyproject.toml" in changed_files

    except RuntimeError as e:
        warn(e)
        return False

def warm_cache():
    """Pre-warm __pycache__ by compiling all modules."""

    compileall.compile_dir(PACKAGE_PATH, force=True, quiet=1)
    print(f"__pycache__ warmed for {PACKAGE_PATH}")

@click.command()
def setup():
    """Performs TomoSAR setup"""
    post_merge_path = PACKAGE_PATH / ".git" / "hooks" / "post-merge"
    if not post_merge_path.exists():
        shutil.copy2(PACKAGE_PATH / "setup" / "post-merge", post_merge_path)
    if pyproject_changed():
        run(["pip", "install", "-e", PROJECT_PATH])
    check_required_binaries()
    warm_cache()

@click.command()
def depedencies():
    """Scan PATH for required binaries"""
    check_required_binaries()

@click.command()
def warmup():
    """Pre-warm __pycache__ by compiling all modules"""
    warm_cache()