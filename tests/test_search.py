import tempfile
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from slskd_transform.search import (
    list_files_with_duration,
    find_close_duration_song,
    remove_hyphens_and_trim,
    search_and_enqueue,
    threaded_search_and_enqueue,
)
from slskd_transform.config import load_config


def _make_config(**overrides):
    defaults = {"api_key": "test", "host": "http://test:5030"}
    defaults.update(overrides)
    return load_config(config_path=Path("/nonexistent"), cli_overrides=defaults)


class TestListFilesWithDuration:
    def test_returns_name_duration_tuples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Song A.flac").touch()
            Path(tmpdir, "Song B.mp3").touch()

            mock_audio = MagicMock()
            mock_audio.info.length = 245.5

            with patch("slskd_transform.search.mutagen.File", return_value=mock_audio):
                result = list_files_with_duration(Path(tmpdir))

            assert len(result) == 2
            names = [r[0] for r in result]
            assert "Song A" in names
            assert "Song B" in names
            for _, duration in result:
                assert duration == 245

    def test_skips_dotfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".hidden.flac").touch()
            Path(tmpdir, "visible.flac").touch()

            mock_audio = MagicMock()
            mock_audio.info.length = 100.0

            with patch("slskd_transform.search.mutagen.File", return_value=mock_audio):
                result = list_files_with_duration(Path(tmpdir))

            assert len(result) == 1
            assert result[0][0] == "visible"

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_files_with_duration(Path(tmpdir))
            assert result == []

    def test_recursive_scanning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "artist", "album")
            subdir.mkdir(parents=True)
            Path(tmpdir, "top.mp3").touch()
            Path(subdir, "nested.flac").touch()

            mock_audio = MagicMock()
            mock_audio.info.length = 180.0

            with patch("slskd_transform.search.mutagen.File", return_value=mock_audio):
                result = list_files_with_duration(Path(tmpdir), recursive=True)

            assert len(result) == 2

    def test_non_recursive_ignores_subdirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "sub")
            subdir.mkdir()
            Path(tmpdir, "top.mp3").touch()
            Path(subdir, "nested.flac").touch()

            mock_audio = MagicMock()
            mock_audio.info.length = 180.0

            with patch("slskd_transform.search.mutagen.File", return_value=mock_audio):
                result = list_files_with_duration(Path(tmpdir), recursive=False)

            assert len(result) == 1
            assert result[0][0] == "top"


class TestFindCloseDurationSong:
    def test_finds_matching_duration(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 240}]},
        ]
        match = find_close_duration_song(results, 242)
        assert match is not None

    def test_no_match_outside_tolerance(self):
        results = [{"files": [{"filename": "song.flac", "length": 240}]}]
        match = find_close_duration_song(results, 300)
        assert match is None

    def test_empty_results(self):
        assert find_close_duration_song([], 200) is None

    def test_missing_length_key(self):
        results = [{"files": [{"filename": "song.flac"}]}]
        assert find_close_duration_song(results, 200) is None

    def test_custom_tolerance(self):
        results = [{"files": [{"filename": "song.flac", "length": 230}]}]
        assert find_close_duration_song(results, 200, tolerance=30) is not None
        assert find_close_duration_song(results, 200, tolerance=10) is None


class TestRemoveHyphensAndTrim:
    def test_basic(self):
        assert remove_hyphens_and_trim("Artist - Song") == "Artist Song"

    def test_multiple_hyphens(self):
        assert remove_hyphens_and_trim("A - B - C") == "A B C"

    def test_no_hyphens(self):
        assert remove_hyphens_and_trim("No Hyphens") == "No Hyphens"

    def test_empty_string(self):
        assert remove_hyphens_and_trim("") == ""


class TestSearchAndEnqueue:
    @patch("slskd_transform.search.time.sleep")
    def test_successful_enqueue(self, mock_sleep):
        config = _make_config()
        client = MagicMock()
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = [
            {"username": "peer1", "files": [{"filename": "song.flac", "length": 200, "size": 5000}]}
        ]
        client.transfers.enqueue.return_value = True

        unfound = []
        search_and_enqueue([("Artist - Song", 200)], unfound, config=config, client=client)
        assert unfound == []
        client.transfers.enqueue.assert_called_once()

    @patch("slskd_transform.search.time.sleep")
    def test_no_match_adds_to_unfound(self, mock_sleep):
        config = _make_config()
        client = MagicMock()
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = [
            {"username": "peer1", "files": [{"filename": "song.flac", "length": 999, "size": 5000}]}
        ]

        unfound = []
        search_and_enqueue([("Song", 200)], unfound, config=config, client=client)
        assert "Song" in unfound


class TestThreadedSearchAndEnqueue:
    @patch("slskd_transform.search.time.sleep")
    @patch("slskd_transform.search.search_and_enqueue")
    def test_distributes_songs(self, mock_search, mock_sleep):
        config = _make_config(num_threads=2)
        client = MagicMock()
        songs = [(f"Song {i}", i * 10) for i in range(10)]

        threaded_search_and_enqueue(songs, [], config=config, client=client)
        assert mock_search.call_count == 2
