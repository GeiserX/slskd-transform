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

## CLI Reference

```
slskd-transform [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH      Path to config.yml
  --host TEXT            slskd host URL
  --api-key TEXT         slskd API key
  --no-verify-ssl        Disable SSL verification
  -t, --threads INTEGER  Number of search threads
  --help                 Show help

Commands:
  search    Search Soulseek for lossless versions and enqueue downloads
  rename    Rename downloaded FLACs using metadata
```

**search options:**
```
  -m, --music-dir PATH   Directory with lossy source files
  -r, --recursive        Scan music directory recursively
  -f, --format TEXT      Target format (default: flac)
  --tolerance INTEGER    Duration match tolerance in seconds
  --timeout INTEGER      Seconds to wait for search results
```

**rename options:**
```
  -s, --source-dir PATH  Directory where slskd downloads land
  -d, --dest-dir PATH    Destination for renamed files
```

