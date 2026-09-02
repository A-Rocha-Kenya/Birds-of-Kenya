"""Load publication metadata and an optional public-facing profile."""

import tomllib
from pathlib import Path


def merge(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def load(metadata_path, profile_path=None):
    metadata = tomllib.loads(Path(metadata_path).read_text(encoding="utf-8"))
    if profile_path:
        profile = tomllib.loads(Path(profile_path).read_text(encoding="utf-8"))
        merge(metadata, profile)
    return metadata
