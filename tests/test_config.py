import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from slskd_transform.config import load_config, SlskdConfig, DEFAULTS


class TestDefaults:
    def test_load_with_no_sources(self):
        """With no config file, no env vars, no overrides — get defaults."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any SLSKD_ env vars
            env = {k: v for k, v in os.environ.items() if not k.startswith("SLSKD_")}
            with patch.dict(os.environ, env, clear=True):
                config = load_config(config_path=Path("/nonexistent/config.yml"))
                assert config.host == "http://127.0.0.1:5030"
                assert config.api_key == ""
                assert config.verify_ssl is False
                assert config.duration_tolerance == 15
                assert config.num_threads == 5
                assert config.search_timeout == 60
                assert config.format == "flac"
                assert config.recursive is False


class TestEnvVars:
    def test_env_overrides_defaults(self):
        env = {
            "SLSKD_HOST": "http://custom:9999",
            "SLSKD_API_KEY": "test-key",
            "SLSKD_VERIFY_SSL": "true",
            "SLSKD_DURATION_TOLERANCE": "30",
            "SLSKD_NUM_THREADS": "10",
            "SLSKD_RECURSIVE": "yes",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config(config_path=Path("/nonexistent/config.yml"))
            assert config.host == "http://custom:9999"
            assert config.api_key == "test-key"
            assert config.verify_ssl is True
            assert config.duration_tolerance == 30
            assert config.num_threads == 10
            assert config.recursive is True

    def test_bool_env_variations(self):
        for truthy in ("true", "1", "yes", "True", "YES"):
            with patch.dict(os.environ, {"SLSKD_VERIFY_SSL": truthy}, clear=False):
                config = load_config(config_path=Path("/nonexistent/config.yml"))
                assert config.verify_ssl is True

        for falsy in ("false", "0", "no", ""):
            with patch.dict(os.environ, {"SLSKD_VERIFY_SSL": falsy}, clear=False):
                config = load_config(config_path=Path("/nonexistent/config.yml"))
                assert config.verify_ssl is False


class TestYamlConfig:
    def test_loads_from_yaml(self):
        import yaml
        config_data = {
            "host": "http://yaml-host:5030",
            "api_key": "yaml-key",
            "num_threads": 8,
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()
            config = load_config(config_path=Path(f.name))
            assert config.host == "http://yaml-host:5030"
            assert config.api_key == "yaml-key"
            assert config.num_threads == 8
        os.unlink(f.name)


class TestCliOverrides:
    def test_cli_overrides_env_and_yaml(self):
        with patch.dict(os.environ, {"SLSKD_HOST": "http://env:5030"}, clear=False):
            config = load_config(
                config_path=Path("/nonexistent/config.yml"),
                cli_overrides={"host": "http://cli:5030", "num_threads": 3}
            )
            assert config.host == "http://cli:5030"
            assert config.num_threads == 3

    def test_none_overrides_are_skipped(self):
        config = load_config(
            config_path=Path("/nonexistent/config.yml"),
            cli_overrides={"host": None, "num_threads": 7}
        )
        assert config.host == "http://127.0.0.1:5030"
        assert config.num_threads == 7
