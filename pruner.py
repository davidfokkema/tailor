import os
import shutil
import sys
import tomllib
from glob import glob
from pathlib import Path


def prune(base_dir, exclude, include):
    excludes = set()
    base_path = Path(base_dir).resolve()
    for rule in exclude:
        excludes |= set(glob(str(base_path / rule), recursive=True))
    for rule in include:
        excludes -= set(glob(str(base_path / rule), recursive=True))

    cwd = Path.cwd()
    for path in excludes:
        if Path(path).resolve().is_relative_to(cwd):
            try:
                if os.path.isdir(path):
                    print(f"Removing tree {path}...")
                    shutil.rmtree(path)
                else:
                    print(f"Removing file {path}...")
                    os.remove(path)
            except FileNotFoundError:
                # parent directory was already pruned
                pass
        else:
            raise RuntimeError(f"Pruned path {path} is outside project directory")


def main():
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    pruner_config = config["tool"]["pruner"][sys.platform]
    prune(pruner_config["base_dir"], pruner_config["exclude"], pruner_config["include"])


if __name__ == "__main__":
    main()
