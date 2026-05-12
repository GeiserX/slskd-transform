import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from slskd_transform.rename import collect_flac_files, extract_metadata, move_and_rename_flac_files


class TestCollectFlacFiles:
    def test_finds_flac_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.flac").touch()
            Path(tmpdir, "other.mp3").touch()
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(subdir, "nested.FLAC").touch()

            result = collect_flac_files(Path(tmpdir))
            assert len(result) == 2

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = collect_flac_files(Path(tmpdir))
            assert result == []

    def test_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "lower.flac").touch()
            Path(tmpdir, "upper.FLAC").touch()
            Path(tmpdir, "mixed.Flac").touch()
            result = collect_flac_files(Path(tmpdir))
            assert len(result) == 3


class TestExtractMetadata:
    @patch("slskd_transform.rename.FLAC")
    def test_extracts_title_and_artist(self, mock_flac_cls):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda key, default: {
            "title": ["My Song"], "artist": ["My Artist"]
        }.get(key, default)
        mock_flac_cls.return_value = mock_audio

        title, artist = extract_metadata(Path("/fake/path.flac"))
        assert title == "My Song"
        assert artist == "My Artist"

    @patch("slskd_transform.rename.FLAC")
    def test_defaults_to_unknown(self, mock_flac_cls):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda key, default: default
        mock_flac_cls.return_value = mock_audio

        title, artist = extract_metadata(Path("/fake/path.flac"))
        assert title == "Unknown"
        assert artist == "Unknown"


class TestMoveAndRenameFlacFiles:
    @patch("slskd_transform.rename.shutil")
    @patch("slskd_transform.rename.extract_metadata")
    def test_moves_with_metadata_name(self, mock_extract, mock_shutil):
        mock_extract.return_value = ("My Song", "My Artist")
        with tempfile.TemporaryDirectory() as dest:
            move_and_rename_flac_files([Path("/source/file.flac")], Path(dest))
            expected = os.path.join(dest, "My Artist - My Song.flac")
            mock_shutil.move.assert_called_once_with(str(Path("/source/file.flac")), expected)

    @patch("slskd_transform.rename.shutil")
    @patch("slskd_transform.rename.extract_metadata")
    def test_empty_list(self, mock_extract, mock_shutil):
        with tempfile.TemporaryDirectory() as dest:
            move_and_rename_flac_files([], Path(dest))
            mock_shutil.move.assert_not_called()
