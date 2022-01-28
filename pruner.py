import os
import shutil
from glob import glob
from pathlib import Path

import toml


def prune(base_dirs, exclude, include):
    excludes = set()
    for base in base_dirs:
        base_path = Path(base).resolve()
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
    with open("pyproject.toml") as f:
        config = toml.load(f)
    pruner_config = config["tool"]["pruner"]
    prune(
        pruner_config["base_dirs"], pruner_config["exclude"], pruner_config["include"]
    )


if __name__ == "__main__":
    main()
