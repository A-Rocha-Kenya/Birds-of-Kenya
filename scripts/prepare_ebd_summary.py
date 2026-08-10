#!/usr/bin/env python3
"""Rebuild the local compact EBD cache without building a release."""

import argparse
import tomllib
from pathlib import Path

from build_release import prepare_ebd, source_paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    prepare_ebd(source_paths(config), config["ebd_version"], force=True)


if __name__ == "__main__":
    main()
