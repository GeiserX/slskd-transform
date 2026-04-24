"""Tests for slskd-transform: main.py and rename-files.py.

Imports the actual module functions (guarded by if __name__ == '__main__')
and tests them with mocked I/O, network calls, and external dependencies.
"""

import pytest
import tempfile
import os
import sys
import csv
import importlib
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from threading import Thread

import main
# rename-files.py has a hyphen so we need importlib
_spec = importlib.util.spec_from_file_location(
    "rename_files",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "rename-files.py"),
)
rename_files = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rename_files)


# ---------------------------------------------------------------------------
# main.py — write_unfound_songs_to_csv
# ---------------------------------------------------------------------------

class TestWriteUnfoundSongsToCsv:
    def test_writes_header_and_songs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "unfound.csv")
            main.write_unfound_songs_to_csv(["Song A", "Song B"], filepath)

            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader[0] == ["Song Name"]
            assert reader[1] == ["Song A"]
            assert reader[2] == ["Song B"]
            assert len(reader) == 3

    def test_writes_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "unfound.csv")
            main.write_unfound_songs_to_csv([], filepath)

            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader == [["Song Name"]]

    def test_writes_special_characters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "unfound.csv")
            main.write_unfound_songs_to_csv(["Song, With Comma", 'Song "Quotes"'], filepath)

            with open(filepath, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            assert reader[1] == ["Song, With Comma"]
            assert reader[2] == ['Song "Quotes"']


# ---------------------------------------------------------------------------
# main.py — list_files_without_ext
# ---------------------------------------------------------------------------

class TestListFilesWithoutExt:
    def test_strips_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Artist - Song.flac").touch()
            Path(tmpdir, "Other - Track.mp3").touch()
            result = main.list_files_without_ext(tmpdir)
            assert "Artist - Song" in result
            assert "Other - Track" in result

    def test_skips_dotfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".hidden").touch()
            Path(tmpdir, "visible.flac").touch()
            result = main.list_files_without_ext(tmpdir)
            assert "visible" in result
            assert len(result) == 1

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main.list_files_without_ext(tmpdir)
            assert result == []

    def test_file_without_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "noext").touch()
            result = main.list_files_without_ext(tmpdir)
            assert "noext" in result

    def test_multiple_dots_in_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "artist.feat.other.flac").touch()
            result = main.list_files_without_ext(tmpdir)
            assert "artist.feat.other" in result


# ---------------------------------------------------------------------------
# main.py — list_files_with_duration
# ---------------------------------------------------------------------------

class TestListFilesWithDuration:
    def test_returns_name_duration_tuples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "Song A.flac").touch()
            Path(tmpdir, "Song B.mp3").touch()

            mock_audio_info = MagicMock()
            mock_audio_info.info.length = 245.5

            with patch("main.mutagen.File", return_value=mock_audio_info):
                result = main.list_files_with_duration(tmpdir)

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

            mock_audio_info = MagicMock()
            mock_audio_info.info.length = 100.0

            with patch("main.mutagen.File", return_value=mock_audio_info):
                result = main.list_files_with_duration(tmpdir)

            assert len(result) == 1
            assert result[0][0] == "visible"

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main.list_files_with_duration(tmpdir)
            assert result == []

    def test_duration_truncated_to_int(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "track.flac").touch()

            mock_audio_info = MagicMock()
            mock_audio_info.info.length = 199.99

            with patch("main.mutagen.File", return_value=mock_audio_info):
                result = main.list_files_with_duration(tmpdir)

            assert result[0][1] == 199


# ---------------------------------------------------------------------------
# main.py — find_close_duration_song
# ---------------------------------------------------------------------------

class TestFindCloseDurationSong:
    def test_finds_matching_duration(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 240}]},
            {"files": [{"filename": "other.flac", "length": 300}]},
        ]
        match = main.find_close_duration_song(results, 242)
        assert match is not None
        assert match["files"][0]["filename"] == "song.flac"

    def test_no_match_outside_tolerance(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 240}]},
        ]
        match = main.find_close_duration_song(results, 300)
        assert match is None

    def test_empty_results(self):
        match = main.find_close_duration_song([], 200)
        assert match is None

    def test_missing_length_key(self):
        results = [
            {"files": [{"filename": "song.flac"}]},
        ]
        match = main.find_close_duration_song(results, 200)
        assert match is None

    def test_tolerance_boundary_exact(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 215}]},
        ]
        match = main.find_close_duration_song(results, 200)
        assert match is not None

    def test_tolerance_boundary_exceeded(self):
        results = [
            {"files": [{"filename": "song.flac", "length": 216}]},
        ]
        match = main.find_close_duration_song(results, 200)
        assert match is None

    def test_result_with_no_files_key(self):
        results = [{"username": "user1"}]
        match = main.find_close_duration_song(results, 200)
        assert match is None

    def test_result_with_empty_files(self):
        results = [{"files": []}]
        match = main.find_close_duration_song(results, 200)
        assert match is None

    def test_returns_first_match(self):
        results = [
            {"files": [{"filename": "first.flac", "length": 200}]},
            {"files": [{"filename": "second.flac", "length": 201}]},
        ]
        match = main.find_close_duration_song(results, 200)
        assert match["files"][0]["filename"] == "first.flac"

    def test_skips_bad_result_finds_good(self):
        results = [
            {"files": [{"filename": "bad.flac"}]},  # no length key
            {"files": [{"filename": "good.flac", "length": 200}]},
        ]
        match = main.find_close_duration_song(results, 200)
        assert match["files"][0]["filename"] == "good.flac"


# ---------------------------------------------------------------------------
# main.py — remove_hyphens_and_trim
# ---------------------------------------------------------------------------

class TestRemoveHyphensAndTrim:
    def test_basic_hyphen_removal(self):
        assert main.remove_hyphens_and_trim("Artist - Song Name") == "Artist Song Name"

    def test_multiple_hyphens(self):
        assert main.remove_hyphens_and_trim("A - B - C") == "A B C"

    def test_no_hyphens(self):
        assert main.remove_hyphens_and_trim("No Hyphens Here") == "No Hyphens Here"

    def test_leading_trailing_spaces(self):
        result = main.remove_hyphens_and_trim(" Artist - Song ")
        assert result == "Artist Song"

    def test_empty_string(self):
        assert main.remove_hyphens_and_trim("") == ""

    def test_only_hyphen(self):
        # Splitting "-" gives ["", ""] which join as " "
        assert main.remove_hyphens_and_trim("-") == " "

    def test_consecutive_hyphens(self):
        # "A--B" splits into ["A", "", "B"] which join as "A  B"
        result = main.remove_hyphens_and_trim("A--B")
        assert result == "A  B"


# ---------------------------------------------------------------------------
# main.py — search_and_enqueue
# ---------------------------------------------------------------------------

class TestSearchAndEnqueue:
    def _make_mock_slskd(self, search_response, search_results, enqueue_return=True):
        mock = MagicMock()
        mock.searches.search_text.return_value = search_response
        mock.searches.search_responses.return_value = search_results
        mock.transfers.enqueue.return_value = enqueue_return
        return mock

    @patch("main.time.sleep")
    def test_successful_enqueue(self, mock_sleep):
        search_resp = {"id": "search-1"}
        search_results = [
            {
                "username": "peer1",
                "files": [{"filename": "song.flac", "length": 200, "size": 5000}],
            }
        ]
        main.slskd = self._make_mock_slskd(search_resp, search_results, enqueue_return=True)

        unfound = []
        main.search_and_enqueue([("Artist - Song", 200)], unfound)

        assert unfound == []
        main.slskd.searches.search_text.assert_called_once()
        main.slskd.transfers.enqueue.assert_called_once_with(
            username="peer1",
            files=[{"filename": "song.flac", "size": 5000}],
        )
        mock_sleep.assert_called_with(60)

    @patch("main.time.sleep")
    def test_no_matching_duration(self, mock_sleep):
        search_resp = {"id": "search-1"}
        search_results = [
            {
                "username": "peer1",
                "files": [{"filename": "song.flac", "length": 999, "size": 5000}],
            }
        ]
        main.slskd = self._make_mock_slskd(search_resp, search_results)

        unfound = []
        main.search_and_enqueue([("Artist - Song", 200)], unfound)

        assert "Artist - Song" in unfound

    @patch("main.time.sleep")
    def test_enqueue_returns_false(self, mock_sleep):
        search_resp = {"id": "search-1"}
        search_results = [
            {
                "username": "peer1",
                "files": [{"filename": "song.flac", "length": 200, "size": 5000}],
            }
        ]
        main.slskd = self._make_mock_slskd(search_resp, search_results, enqueue_return=False)

        unfound = []
        main.search_and_enqueue([("Artist - Song", 200)], unfound)

        assert "Artist - Song" in unfound

    @patch("main.time.sleep")
    def test_enqueue_http_error(self, mock_sleep):
        import requests

        search_resp = {"id": "search-1"}
        search_results = [
            {
                "username": "peer1",
                "files": [{"filename": "song.flac", "length": 200, "size": 5000}],
            }
        ]
        mock_slskd = self._make_mock_slskd(search_resp, search_results)
        mock_slskd.transfers.enqueue.side_effect = requests.exceptions.HTTPError("500")
        main.slskd = mock_slskd

        unfound = []
        main.search_and_enqueue([("Artist - Song", 200)], unfound)

        assert "Artist - Song" in unfound

    @patch("main.time.sleep")
    def test_multiple_songs(self, mock_sleep):
        search_resp = {"id": "search-1"}
        # First song found, second not
        main.slskd = MagicMock()
        main.slskd.searches.search_text.return_value = search_resp

        good_results = [
            {
                "username": "peer1",
                "files": [{"filename": "song1.flac", "length": 200, "size": 5000}],
            }
        ]
        bad_results = [
            {
                "username": "peer2",
                "files": [{"filename": "song2.flac", "length": 999, "size": 5000}],
            }
        ]
        main.slskd.searches.search_responses.side_effect = [good_results, bad_results]
        main.slskd.transfers.enqueue.return_value = True

        unfound = []
        main.search_and_enqueue(
            [("Song One", 200), ("Song Two", 100)], unfound
        )

        assert len(unfound) == 1
        assert "Song Two" in unfound

    @patch("main.time.sleep")
    def test_search_text_includes_flac(self, mock_sleep):
        search_resp = {"id": "search-1"}
        main.slskd = self._make_mock_slskd(search_resp, [], enqueue_return=True)

        unfound = []
        main.search_and_enqueue([("My Song", 200)], unfound)

        call_args = main.slskd.searches.search_text.call_args
        assert "flac" in call_args[1]["searchText"]

    @patch("main.time.sleep")
    def test_empty_song_list(self, mock_sleep):
        main.slskd = MagicMock()
        unfound = []
        main.search_and_enqueue([], unfound)
        assert unfound == []
        main.slskd.searches.search_text.assert_not_called()


# ---------------------------------------------------------------------------
# main.py — threaded_search_and_enqueue
# ---------------------------------------------------------------------------

class TestThreadedSearchAndEnqueue:
    @patch("main.time.sleep")
    @patch("main.search_and_enqueue")
    def test_distributes_songs_across_threads(self, mock_search, mock_sleep):
        songs = [(f"Song {i}", i * 10) for i in range(10)]
        unfound = []

        main.threaded_search_and_enqueue(songs, unfound, num_threads=2)

        assert mock_search.call_count == 2
        # First chunk: 5 songs, second chunk: remaining 5
        first_chunk = mock_search.call_args_list[0][0][0]
        second_chunk = mock_search.call_args_list[1][0][0]
        assert len(first_chunk) + len(second_chunk) == 10

    @patch("main.time.sleep")
    @patch("main.search_and_enqueue")
    def test_single_thread(self, mock_search, mock_sleep):
        songs = [("Song A", 100), ("Song B", 200)]
        unfound = []

        main.threaded_search_and_enqueue(songs, unfound, num_threads=1)

        assert mock_search.call_count == 1
        chunk = mock_search.call_args_list[0][0][0]
        assert len(chunk) == 2

    @patch("main.time.sleep")
    @patch("main.search_and_enqueue")
    def test_last_thread_gets_remainder(self, mock_search, mock_sleep):
        songs = [(f"Song {i}", i * 10) for i in range(7)]
        unfound = []

        main.threaded_search_and_enqueue(songs, unfound, num_threads=3)

        assert mock_search.call_count == 3
        chunks = [c[0][0] for c in mock_search.call_args_list]
        total = sum(len(c) for c in chunks)
        assert total == 7
        # Last chunk should have the remainder
        assert len(chunks[2]) >= len(chunks[0])

    @patch("main.time.sleep")
    @patch("main.search_and_enqueue")
    def test_sleeps_between_thread_starts(self, mock_search, mock_sleep):
        songs = [(f"Song {i}", i * 10) for i in range(6)]
        unfound = []

        main.threaded_search_and_enqueue(songs, unfound, num_threads=3)

        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        assert sleep_calls.count(10) == 3


# ---------------------------------------------------------------------------
# main.py — main()
# ---------------------------------------------------------------------------

class TestMainFunction:
    @patch("main.write_unfound_songs_to_csv")
    @patch("main.threaded_search_and_enqueue")
    @patch("main.list_files_with_duration", return_value=[("Song", 200)])
    @patch("main.slskd_api.SlskdClient")
    def test_main_no_unfound(self, mock_client, mock_list, mock_threaded, mock_csv):
        mock_threaded.side_effect = lambda songs, unfound, **kw: None
        main.main()

        mock_client.assert_called_once()
        mock_list.assert_called_once()
        mock_threaded.assert_called_once()
        mock_csv.assert_not_called()

    @patch("main.write_unfound_songs_to_csv")
    @patch("main.threaded_search_and_enqueue")
    @patch("main.list_files_with_duration", return_value=[("Song", 200)])
    @patch("main.slskd_api.SlskdClient")
    def test_main_with_unfound(self, mock_client, mock_list, mock_threaded, mock_csv):
        def add_unfound(songs, unfound, **kw):
            unfound.append("Lost Song")

        mock_threaded.side_effect = add_unfound
        main.main()

        mock_csv.assert_called_once_with(["Lost Song"], "unfound_songs.csv")


# ---------------------------------------------------------------------------
# rename-files.py — collect_flac_files
# ---------------------------------------------------------------------------

class TestCollectFlacFiles:
    def test_finds_flac_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.flac").touch()
            Path(tmpdir, "other.mp3").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "nested.FLAC").touch()

            result = rename_files.collect_flac_files(tmpdir)
            assert len(result) == 2
            names = [os.path.basename(f) for f in result]
            assert "song.flac" in names
            assert "nested.FLAC" in names
            assert "other.mp3" not in names

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = rename_files.collect_flac_files(tmpdir)
            assert result == []

    def test_deeply_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deep = Path(tmpdir, "a", "b", "c")
            deep.mkdir(parents=True)
            Path(deep, "deep.flac").touch()
            result = rename_files.collect_flac_files(tmpdir)
            assert len(result) == 1
            assert "deep.flac" in result[0]

    def test_case_insensitive_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "lower.flac").touch()
            Path(tmpdir, "upper.FLAC").touch()
            Path(tmpdir, "mixed.Flac").touch()
            result = rename_files.collect_flac_files(tmpdir)
            assert len(result) == 3

    def test_ignores_non_flac(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.mp3").touch()
            Path(tmpdir, "song.wav").touch()
            Path(tmpdir, "song.ogg").touch()
            Path(tmpdir, "song.flac.txt").touch()
            result = rename_files.collect_flac_files(tmpdir)
            assert result == []


# ---------------------------------------------------------------------------
# rename-files.py — extract_metadata
# ---------------------------------------------------------------------------

class TestExtractMetadata:
    @patch.object(rename_files, "FLAC")
    def test_extracts_title_and_artist(self, mock_flac_cls):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda key, default: {
            "title": ["My Song"],
            "artist": ["My Artist"],
        }.get(key, default)
        mock_flac_cls.return_value = mock_audio

        title, artist = rename_files.extract_metadata("/fake/path.flac")
        assert title == "My Song"
        assert artist == "My Artist"

    @patch.object(rename_files, "FLAC")
    def test_defaults_to_unknown(self, mock_flac_cls):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda key, default: default
        mock_flac_cls.return_value = mock_audio

        title, artist = rename_files.extract_metadata("/fake/path.flac")
        assert title == "Unknown"
        assert artist == "Unknown"


# ---------------------------------------------------------------------------
# rename-files.py — sanitize_filename
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert rename_files.sanitize_filename('Song: "Title"') == "Song Title"
        assert rename_files.sanitize_filename("A/B\\C") == "ABC"
        assert rename_files.sanitize_filename("normal.flac") == "normal.flac"

    def test_removes_all_special_chars(self):
        result = rename_files.sanitize_filename("A*B?C<D>E|F")
        assert "*" not in result
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_preserves_valid_chars(self):
        assert (
            rename_files.sanitize_filename("Hello World - Track 01.flac")
            == "Hello World - Track 01.flac"
        )

    def test_empty_string(self):
        assert rename_files.sanitize_filename("") == ""

    def test_all_invalid(self):
        assert rename_files.sanitize_filename('\\/:*?"<>|') == ""


# ---------------------------------------------------------------------------
# rename-files.py — move_and_rename_flac_files
# ---------------------------------------------------------------------------

class TestMoveAndRenameFlacFiles:
    @patch.object(rename_files, "shutil")
    @patch.object(rename_files, "extract_metadata")
    def test_moves_files_with_metadata_name(self, mock_extract, mock_shutil):
        mock_extract.return_value = ("My Song", "My Artist")

        with tempfile.TemporaryDirectory() as dest:
            rename_files.move_and_rename_flac_files(
                ["/source/file.flac"], dest
            )

            expected_path = os.path.join(dest, "My Artist - My Song.flac")
            mock_shutil.move.assert_called_once_with("/source/file.flac", expected_path)

    @patch.object(rename_files, "shutil")
    @patch.object(rename_files, "extract_metadata")
    def test_sanitizes_filename(self, mock_extract, mock_shutil):
        mock_extract.return_value = ('Song: "Special"', "Art/ist")

        with tempfile.TemporaryDirectory() as dest:
            rename_files.move_and_rename_flac_files(
                ["/source/file.flac"], dest
            )

            expected_path = os.path.join(dest, "Artist - Song Special.flac")
            mock_shutil.move.assert_called_once_with("/source/file.flac", expected_path)

    @patch.object(rename_files, "shutil")
    @patch.object(rename_files, "extract_metadata")
    def test_multiple_files(self, mock_extract, mock_shutil):
        mock_extract.side_effect = [
            ("Song A", "Artist A"),
            ("Song B", "Artist B"),
        ]

        with tempfile.TemporaryDirectory() as dest:
            rename_files.move_and_rename_flac_files(
                ["/source/a.flac", "/source/b.flac"], dest
            )

            assert mock_shutil.move.call_count == 2

    @patch.object(rename_files, "shutil")
    @patch.object(rename_files, "extract_metadata")
    def test_empty_file_list(self, mock_extract, mock_shutil):
        with tempfile.TemporaryDirectory() as dest:
            rename_files.move_and_rename_flac_files([], dest)
            mock_shutil.move.assert_not_called()
            mock_extract.assert_not_called()


# ---------------------------------------------------------------------------
# rename-files.py — main()
# ---------------------------------------------------------------------------

class TestRenameFilesMain:
    @patch.object(rename_files, "move_and_rename_flac_files")
    @patch.object(rename_files, "collect_flac_files", return_value=["/dl/song.flac"])
    def test_main_calls_pipeline(self, mock_collect, mock_move):
        rename_files.main()

        mock_collect.assert_called_once_with("G:\\slskd\\downloads")
        mock_move.assert_called_once_with(["/dl/song.flac"], "G:\\slskd\\")
