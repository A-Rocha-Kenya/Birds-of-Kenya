#!/usr/bin/env python3
"""Download a pinned eBird taxonomy CSV for a release build."""

import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="eBird taxonomy version, for example 2025")
    parser.add_argument("output", type=Path)
    parser.add_argument("--insecure", action="store_true", help="allow curl to bypass a local certificate-chain problem")
    args = parser.parse_args()
    url = f"https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=csv&locale=en&version={args.version}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = ["curl", "--fail", "--silent", "--show-error", "--location", url, "--output", str(args.output)]
    if args.insecure:
        command.insert(1, "--insecure")
    subprocess.run(command, check=True)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
