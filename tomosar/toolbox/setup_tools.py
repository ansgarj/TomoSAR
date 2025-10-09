import click
import compileall
import tomosar
import shutil
from pathlib import Path

from tomosar.utils import warn
from tomosar.binaries import check_required_binaries, run

PACKAGE_PATH = Path(tomosar.__file__).parent
PROJECT_PATH = Path(tomosar.__file__).parent.parent

def pyproject_changed() -> bool:
    """Checks whether pyproject.toml was changed in the last merge (pull)"""
    try:
        # Run the git diff-tree command
        result = run(["git", "diff-tree", "-r", "--name-only", "--no-commit-id", "ORIG_HEAD", "HEAD"])
        
        # Check if pyproject.toml is in the output
        changed_files = result.stdout.splitlines()
        return "pyproject.toml" in changed_files

    except RuntimeError as e:
        try: 
            # Run git diff-tree against last commit instead
            result =run(["git", "diff-tree", "-r", "--name-only", "--no-commit-id", "HEAD~1", "HEAD"])

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
    post_merge_path = PROJECT_PATH / ".git" / "hooks" / "post-merge"
    if not post_merge_path.exists():
        shutil.copy2(PROJECT_PATH / "setup" / "post-merge", post_merge_path)
        print("Project post-merge hook installed.")
    if pyproject_changed():
        run(["pip", "install", "-e", PROJECT_PATH])
    else:
        print("Installation up to speed, no action required.")
    check_required_binaries()
    warm_cache()

@click.command()
def dependencies():
    """Scan PATH for required binaries"""
    check_required_binaries()

@click.command()
def warmup():
    """Pre-warm __pycache__ by compiling all modules"""
    warm_cache()