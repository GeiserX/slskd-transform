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
