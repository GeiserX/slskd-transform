# Configuration

slskd-transform loads configuration from multiple sources with this priority:

```
CLI flags  >  Environment variables  >  Config file  >  Defaults
```

## Config File

Create `config.yml` in the directory you run the command from, or at `~/.config/slskd-transform/config.yml`, or pass any path with `--config`. The first file found wins; the two locations are not merged. Keys the tool does not know are ignored without a warning, so check the spelling against this file, the repository's `config.example.yml`:

```yaml
--8<-- "config.example.yml"
```

## Environment Variables

All settings can be configured via `SLSKD_` prefixed environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SLSKD_HOST` | slskd instance URL | `http://127.0.0.1:5030` |
| `SLSKD_API_KEY` | slskd API key | -- |
| `SLSKD_VERIFY_SSL` | Enable SSL verification | `false` |
| `SLSKD_MUSIC_DIR` | Source directory with lossy files | `./music` |
| `SLSKD_DURATION_TOLERANCE` | Max duration difference (seconds) | `15` |
| `SLSKD_NUM_THREADS` | Concurrent search threads | `5` |
| `SLSKD_SEARCH_TIMEOUT` | Wait time for search results (seconds) | `60` |
| `SLSKD_FORMAT` | Target format to search for | `flac` |
| `SLSKD_RECURSIVE` | Scan directories recursively | `false` |
| `SLSKD_SOURCE_DIR` | Download directory for rename | `./downloads` |
| `SLSKD_DESTINATION_DIR` | Output directory for rename | `./organized` |

Every flag is listed in [Usage](usage.md#command-reference).
