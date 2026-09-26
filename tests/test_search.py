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
    run_search,
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


def _fake_mutagen_file(path, easy=True):
    """Stand-in for mutagen.File keyed on the file name."""
    name = os.path.basename(path)
    if name.startswith("broken"):
        import mutagen
        raise mutagen.MutagenError("corrupt")
    if name.startswith("notaudio"):
        return None
    if name.startswith("noinfo"):
        audio = MagicMock()
        audio.info = None
        return audio
    audio = MagicMock()
    audio.info.length = 200.0
    return audio


class TestListFilesSkipsUnreadable:
    def test_flat_skips_unreadable_and_non_audio(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("good.mp3", "broken.mp3", "notaudio.txt", "noinfo.mp3"):
                Path(tmpdir, name).touch()

            with patch("slskd_transform.search.mutagen.File", side_effect=_fake_mutagen_file):
                result = list_files_with_duration(Path(tmpdir))

            assert result == [("good", 200)]

    def test_recursive_skips_dotfiles_unreadable_and_non_audio(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "album")
            subdir.mkdir()
            for name in ("good.mp3", ".hidden.mp3", "broken.mp3", "notaudio.txt", "noinfo.mp3"):
                Path(subdir, name).touch()

            with patch("slskd_transform.search.mutagen.File", side_effect=_fake_mutagen_file):
                result = list_files_with_duration(Path(tmpdir), recursive=True)

            assert result == [("good", 200)]


class TestSearchAndEnqueueFailures:
    def _client_with_match(self):
        client = MagicMock()
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = [
            {"username": "peer1", "files": [{"filename": "song.flac", "length": 200, "size": 5000}]}
        ]
        return client

    @patch("slskd_transform.search.time.sleep")
    def test_rejected_enqueue_adds_to_unfound(self, mock_sleep):
        client = self._client_with_match()
        client.transfers.enqueue.return_value = False

        unfound = []
        search_and_enqueue([("Artist - Song", 200)], unfound, config=_make_config(), client=client)
        assert unfound == ["Artist - Song"]

    @patch("slskd_transform.search.time.sleep")
    def test_http_error_adds_to_unfound_and_continues(self, mock_sleep):
        import requests

        client = self._client_with_match()
        client.transfers.enqueue.side_effect = [requests.exceptions.HTTPError("500"), True]

        unfound = []
        search_and_enqueue(
            [("First", 200), ("Second", 200)], unfound, config=_make_config(), client=client
        )
        assert unfound == ["First"]
        assert client.transfers.enqueue.call_count == 2

    @patch("slskd_transform.search.time.sleep")
    def test_searches_with_format_and_waits_for_timeout(self, mock_sleep):
        client = self._client_with_match()
        client.transfers.enqueue.return_value = True

        config = _make_config(format="wav", search_timeout=7)
        search_and_enqueue([("Artist - Song", 200)], [], config=config, client=client)
        client.searches.search_text.assert_called_once_with(searchText="Artist Song wav")
        mock_sleep.assert_called_once_with(7)
        client.transfers.enqueue.assert_called_once_with(
            username="peer1", files=[{"filename": "song.flac", "size": 5000}]
        )


class TestThreadedSearchEdgeCases:
    @patch("slskd_transform.search.Thread")
    def test_empty_list_starts_no_threads(self, mock_thread):
        threaded_search_and_enqueue([], [], config=_make_config(), client=MagicMock())
        mock_thread.assert_not_called()

    @patch("slskd_transform.search.time.sleep")
    def test_collects_unfound_from_every_thread(self, mock_sleep):
        client = MagicMock()
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = []
        songs = [(f"Song {i}", 100) for i in range(5)]

        unfound = []
        threaded_search_and_enqueue(songs, unfound, config=_make_config(num_threads=2), client=client)
        assert sorted(unfound) == [f"Song {i}" for i in range(5)]


class TestRunSearch:
    @patch("slskd_transform.search.time.sleep")
    @patch("slskd_transform.search.slskd_api.SlskdClient")
    def test_writes_csv_of_unfound_songs(self, mock_client_cls, mock_sleep):
        client = mock_client_cls.return_value
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Artist - Missing.mp3").touch()
            config = _make_config(music_dir=tmpdir, verify_ssl=True)

            with patch("slskd_transform.search.mutagen.File", side_effect=_fake_mutagen_file):
                run_search(config)

            mock_client_cls.assert_called_once_with(
                host="http://test:5030", api_key="test", verify_ssl=True
            )
            csv_path = Path(tmpdir, "unfound_songs.csv")
            assert csv_path.read_text(encoding="utf-8").splitlines() == [
                "Song Name",
                "Artist - Missing",
            ]

    @patch("slskd_transform.search.time.sleep")
    @patch("slskd_transform.search.slskd_api.SlskdClient")
    def test_no_csv_when_everything_is_found(self, mock_client_cls, mock_sleep):
        client = mock_client_cls.return_value
        client.searches.search_text.return_value = {"id": "s1"}
        client.searches.search_responses.return_value = [
            {"username": "peer1", "files": [{"filename": "song.flac", "length": 200, "size": 5000}]}
        ]
        client.transfers.enqueue.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Artist - Found.mp3").touch()
            config = _make_config(music_dir=tmpdir)

            with patch("slskd_transform.search.mutagen.File", side_effect=_fake_mutagen_file):
                run_search(config)

            assert not Path(tmpdir, "unfound_songs.csv").exists()
            client.transfers.enqueue.assert_called_once()
