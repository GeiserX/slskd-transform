"""Rename and organize downloaded FLAC files by metadata."""

import os
import shutil
from pathlib import Path

from mutagen.flac import FLAC

from slskd_transform.config import SlskdConfig
from slskd_transform.utils import sanitize_filename


def collect_flac_files(directory: Path) -> list[Path]:
    """Recursively collect all .flac files (case-insensitive) under directory."""
    flac_files = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".flac"):
                flac_files.append(Path(root) / file)
    return flac_files


def extract_metadata(file_path: Path) -> tuple[str, str]:
    """Read FLAC tags, return (title, artist). Defaults to 'Unknown' if missing."""
    audio = FLAC(str(file_path))
    title = audio.get("title", ["Unknown"])[0]
    artist = audio.get("artist", ["Unknown"])[0]
    return title, artist


def move_and_rename_flac_files(flac_files: list[Path], destination: Path) -> None:
    """Move each file to destination as 'Artist - Title.flac' (sanitized)."""
    for file in flac_files:
        title, artist = extract_metadata(file)
        new_filename = sanitize_filename(f"{artist} - {title}.flac")
        shutil.move(str(file), str(destination / new_filename))
        print(f"Moved and renamed: {destination / new_filename}")


def run_rename(config: SlskdConfig) -> None:
    """Top-level orchestrator: collect files from source_dir, rename to destination_dir."""
    config.destination_dir.mkdir(parents=True, exist_ok=True)
    flac_files = collect_flac_files(config.source_dir)
    move_and_rename_flac_files(flac_files, config.destination_dir)
