# Configuration

slskd-transform loads configuration from multiple sources with this priority:

```
CLI flags  >  Environment variables  >  Config file  >  Defaults
```

## Config File

Create `config.yml` in your working directory or `~/.config/slskd-transform/config.yml`:

```yaml
# slskd connection
host: "http://127.0.0.1:5030"
api_key: "your-api-key"
verify_ssl: false

# Search settings
music_dir: "./music"
duration_tolerance: 15
num_threads: 5
search_timeout: 60
format: "flac"
recursive: false

# Rename settings
source_dir: "./downloads"
destination_dir: "./organized"
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
