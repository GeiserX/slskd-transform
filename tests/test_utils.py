import csv
import tempfile
import os
from pathlib import Path

from slskd_transform.utils import write_unfound_songs_to_csv, sanitize_filename


class TestWriteUnfoundSongsToCsv:
    def test_writes_header_and_songs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "unfound.csv"
            write_unfound_songs_to_csv(["Song A", "Song B"], filepath)
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader[0] == ["Song Name"]
            assert reader[1] == ["Song A"]
            assert reader[2] == ["Song B"]

    def test_writes_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "unfound.csv"
            write_unfound_songs_to_csv([], filepath)
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader == [["Song Name"]]

    def test_writes_special_characters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "unfound.csv"
            write_unfound_songs_to_csv(["Song, With Comma", 'Song "Quotes"'], filepath)
            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader[1] == ["Song, With Comma"]
            assert reader[2] == ['Song "Quotes"']


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert sanitize_filename('Song: "Title"') == "Song Title"
        assert sanitize_filename("A/B\\C") == "ABC"
        assert sanitize_filename("normal.flac") == "normal.flac"

    def test_removes_all_special_chars(self):
        result = sanitize_filename("A*B?C<D>E|F")
        assert "*" not in result
        assert "?" not in result

    def test_preserves_valid_chars(self):
        assert sanitize_filename("Hello World - Track 01.flac") == "Hello World - Track 01.flac"

    def test_empty_string(self):
        assert sanitize_filename("") == ""

    def test_all_invalid(self):
        assert sanitize_filename('\\/:*?"<>|') == ""
