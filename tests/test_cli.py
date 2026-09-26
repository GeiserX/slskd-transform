from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from slskd_transform.cli import cli


class TestCliSearch:
    @patch("slskd_transform.cli.run_search")
    @patch("slskd_transform.cli.load_config")
    def test_search_with_api_key(self, mock_load, mock_run):
        mock_load.return_value = MagicMock(api_key="test-key")
        runner = CliRunner()
        result = runner.invoke(cli, ["--api-key", "test-key", "search"])
        assert result.exit_code == 0
        mock_run.assert_called_once()

    @patch("slskd_transform.cli.load_config")
    def test_search_without_api_key_fails(self, mock_load):
        mock_load.return_value = MagicMock(api_key="")
        runner = CliRunner()
        result = runner.invoke(cli, ["search"])
        assert result.exit_code != 0
        assert "API key" in result.output


class TestCliRename:
    @patch("slskd_transform.cli.run_rename")
    @patch("slskd_transform.cli.load_config")
    def test_rename_runs(self, mock_load, mock_run):
        mock_load.return_value = MagicMock()
        runner = CliRunner()
        result = runner.invoke(cli, ["rename"])
        assert result.exit_code == 0
        mock_run.assert_called_once()


class TestCliOverrides:
    @patch("slskd_transform.cli.run_search")
    @patch("slskd_transform.cli.load_config")
    def test_search_options_become_overrides(self, mock_load, mock_run, tmp_path):
        mock_load.return_value = MagicMock(api_key="k")
        music = str(tmp_path)
        result = CliRunner().invoke(cli, [
            "--host", "http://h:5030", "--api-key", "k", "--no-verify-ssl", "--threads", "3",
            "search", "--music-dir", music, "--recursive", "--format", "mp3",
            "--tolerance", "7", "--timeout", "12",
        ])
        assert result.exit_code == 0, result.output
        assert mock_load.call_args.kwargs["cli_overrides"] == {
            "host": "http://h:5030",
            "api_key": "k",
            "verify_ssl": False,
            "num_threads": 3,
            "music_dir": music,
            "recursive": True,
            "format": "mp3",
            "duration_tolerance": 7,
            "search_timeout": 12,
        }

    @patch("slskd_transform.cli.run_rename")
    @patch("slskd_transform.cli.load_config")
    def test_rename_options_become_overrides(self, mock_load, mock_run, tmp_path):
        source, dest = str(tmp_path), str(tmp_path / "out")
        result = CliRunner().invoke(cli, ["rename", "--source-dir", source, "--dest-dir", dest])
        assert result.exit_code == 0, result.output
        assert mock_load.call_args.kwargs["cli_overrides"] == {
            "source_dir": source,
            "destination_dir": dest,
        }

    @patch("slskd_transform.cli.run_search")
    @patch("slskd_transform.cli.load_config")
    def test_config_path_is_passed_through(self, mock_load, mock_run, tmp_path):
        mock_load.return_value = MagicMock(api_key="k")
        config_file = tmp_path / "config.yml"
        config_file.write_text("api_key: k\n")
        result = CliRunner().invoke(cli, ["--config", str(config_file), "search"])
        assert result.exit_code == 0, result.output
        assert mock_load.call_args.kwargs["config_path"] == config_file
        assert mock_load.call_args.kwargs["cli_overrides"] == {}
