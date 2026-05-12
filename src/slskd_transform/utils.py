import csv
from pathlib import Path


def write_unfound_songs_to_csv(unfound_songs: list[str], filepath: Path) -> None:
    """Write unfound song names to a CSV file with a 'Song Name' header."""
    with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Song Name'])
        for song in unfound_songs:
            csv_writer.writerow([song])


def sanitize_filename(filename: str) -> str:
    """Remove characters invalid on Windows/Linux filesystems: \\/:*?"<>|"""
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename
