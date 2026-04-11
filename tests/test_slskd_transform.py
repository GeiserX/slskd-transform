"""Tests for slskd-transform file matching and rename logic.

Tests the pure logic functions without importing the full modules
(which have top-level code with side effects like network calls and sleeps).
"""

import pytest
import tempfile
import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Helper: re-implement the pure functions from main.py to test their logic
# (main.py cannot be safely imported due to top-level side effects)
# ---------------------------------------------------------------------------

def list_files_without_ext(music_dir):
    """Copied from main.py for testability."""
    filenames = []
    for file in os.listdir(music_dir):
        if not file.startswith('.'):
            file_without_ext = os.path.splitext(file)[0]
            filenames.append(file_without_ext)
    return filenames


def find_close_duration_song(search_results, local_duration):
    """Copied from main.py for testability."""
    duration_tolerance = 15
    for result in search_results:
        if 'files' in result and len(result['files']) > 0:
            file_info = result['files'][0]
            try:
                result_duration = int(file_info['length'])
                if abs(local_duration - result_duration) <= duration_tolerance:
                    return result
            except KeyError:
                pass
    return None


def remove_hyphens_and_trim(song_name):
    """Copied from main.py for testability."""
    return ' '.join(segment.strip() for segment in song_name.split('-'))


def sanitize_filename(filename):
    """Copied from rename-files.py for testability."""
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename


def collect_flac_files(directory):
    """Copied from rename-files.py for testability."""
    flac_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.flac'):
                flac_files.append(os.path.join(root, file))
    return flac_files


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestListFilesWithoutExt:
    def test_strips_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Artist - Song.flac").touch()
            Path(tmpdir, "Other - Track.mp3").touch()
            result = list_files_without_ext(tmpdir)
            assert "Artist - Song" in result
            assert "Other - Track" in result

    def test_skips_dotfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".hidden").touch()
            Path(tmpdir, "visible.flac").touch()
            result = list_files_without_ext(tmpdir)
            assert "visible" in result
            assert ".hidden" not in result
            assert len(result) == 1

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_files_without_ext(tmpdir)
            assert result == []


class TestRemoveHyphensAndTrim:
    def test_basic_hyphen_removal(self):
        assert remove_hyphens_and_trim("Artist - Song Name") == "Artist Song Name"

    def test_multiple_hyphens(self):
        assert remove_hyphens_and_trim("A - B - C") == "A B C"

    def test_no_hyphens(self):
        assert remove_hyphens_and_trim("No Hyphens Here") == "No Hyphens Here"

    def test_leading_trailing_spaces(self):
        result = remove_hyphens_and_trim(" Artist - Song ")
        assert result == "Artist Song"


class TestFindCloseDurationSong:
    def test_finds_matching_duration(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 240}]},
            {"files": [{"filename": "other.flac", "length": 300}]},
        ]
        match = find_close_duration_song(results, 242)
        assert match is not None
        assert match["files"][0]["filename"] == "song.flac"

    def test_no_match_outside_tolerance(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 240}]},
        ]
        match = find_close_duration_song(results, 300)
        assert match is None

    def test_empty_results(self):
        match = find_close_duration_song([], 200)
        assert match is None

    def test_missing_length_key(self):
        results = [
            {"files": [{"filename": "song.flac"}]},
        ]
        match = find_close_duration_song(results, 200)
        assert match is None

    def test_tolerance_boundary_exact(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 215}]},
        ]
        # Exactly at tolerance (15 seconds)
        match = find_close_duration_song(results, 200)
        assert match is not None

    def test_tolerance_boundary_exceeded(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 216}]},
        ]
        # Beyond tolerance (16 > 15)
        match = find_close_duration_song(results, 200)
        assert match is None

    def test_result_with_no_files_key(self):
        results = [
            {"username": "user1"},
        ]
        match = find_close_duration_song(results, 200)
        assert match is None

    def test_result_with_empty_files(self):
        results = [
            {"files": []},
        ]
        match = find_close_duration_song(results, 200)
        assert match is None


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert sanitize_filename('Song: "Title"') == 'Song Title'
        assert sanitize_filename("A/B\\C") == "ABC"
        assert sanitize_filename("normal.flac") == "normal.flac"

    def test_removes_all_special_chars(self):
        result = sanitize_filename('A*B?C<D>E|F')
        assert '*' not in result
        assert '?' not in result
        assert '<' not in result
        assert '>' not in result
        assert '|' not in result

    def test_preserves_valid_chars(self):
        assert sanitize_filename("Hello World - Track 01.flac") == "Hello World - Track 01.flac"


class TestCollectFlacFiles:
    def test_finds_flac_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.flac").touch()
            Path(tmpdir, "other.mp3").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "nested.FLAC").touch()

            result = collect_flac_files(tmpdir)
            assert len(result) == 2
            names = [os.path.basename(f) for f in result]
            assert "song.flac" in names
            assert "nested.FLAC" in names
            assert "other.mp3" not in names

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = collect_flac_files(tmpdir)
            assert result == []

    def test_deeply_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deep = Path(tmpdir, "a", "b", "c")
            deep.mkdir(parents=True)
            Path(deep, "deep.flac").touch()
            result = collect_flac_files(tmpdir)
            assert len(result) == 1
            assert "deep.flac" in result[0]
