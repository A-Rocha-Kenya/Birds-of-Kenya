#!/usr/bin/env python3
"""Export a taxonomy-only comparison between any two archived checklist versions."""

import argparse
import json
from pathlib import Path

from site_archive import load_archive, write_comparison
from taxonomy_comparison import compare_versions

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="archived source release ID")
    parser.add_argument("target", help="archived target release ID")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview-release", help="explicitly include a draft snapshot")
    args = parser.parse_args()
    _, bundles = load_archive(ROOT, args.preview_release)
    versions = {identifier: json.loads((path / "taxonomy.json").read_text()) for identifier, (path, _) in bundles.items()}
    transitions = [json.loads((path / "transition.json").read_text()) for path, _ in bundles.values() if (path / "transition.json").exists()]
    pair = compare_versions(versions, transitions, args.source, args.target)
    write_comparison(args.output, pair)
    print(f"Exported {pair['group_count']} taxonomic changes: {args.source} → {args.target}")


if __name__ == "__main__":
    main()
