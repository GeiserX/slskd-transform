<p align="center">
  <img src="docs/images/banner.svg" alt="slskd-transform banner" width="900"/>
</p>

<p align="center">
  <strong>Bulk-upgrade your music library from lossy to lossless via Soulseek</strong>
</p>

<p align="center">
  <a href="https://github.com/GeiserX/slskd-transform/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GeiserX/slskd-transform?style=flat-square&color=FF6F00" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/slskd/slskd"><img src="https://img.shields.io/badge/requires-slskd-1A1A2E?style=flat-square" alt="Requires slskd"></a>
  <a href="https://github.com/GeiserX/slskd-transform/stargazers"><img src="https://img.shields.io/github/stars/GeiserX/slskd-transform?style=flat-square&color=FFD54F" alt="Stars"></a>
  <a href="https://codecov.io/gh/GeiserX/slskd-transform"><img src="https://img.shields.io/codecov/c/github/GeiserX/slskd-transform?style=flat-square" alt="Coverage"></a>
</p>

---

**slskd-transform** scans your local music library, searches the [Soulseek](https://www.slsknet.org/) network through [slskd](https://github.com/slskd/slskd) for matching FLAC versions of each track, and automatically enqueues them for download. It matches songs by **audio duration** rather than filenames alone, ensuring you get the correct track every time.

A companion `rename` command handles post-download organization, renaming all downloaded FLACs into a clean `Artist - Title.flac` structure using embedded metadata.

## Features

- **Duration-based matching** -- Compares local track duration against search results with a configurable tolerance (default: 15 seconds).
- **Recursive scanning** -- Point it at your existing music library with `--recursive`, no need to flatten files first.
- **Multi-threaded search** -- Distributes searches across multiple threads (default: 5) for faster processing.
- **Flexible configuration** -- Config file, environment variables, or CLI flags. No code editing required.
- **Automatic enqueue** -- Matched FLAC files are enqueued for download directly through the slskd API.
- **CSV reporting** -- Tracks that could not be found are written to `unfound_songs.csv`.
- **Metadata-based renaming** -- Reads FLAC tags and renames files to `Artist - Title.flac`.
- **Docker support** -- Run alongside slskd in the same compose stack.

## Prerequisites

- **Python 3.10+**
- **[slskd](https://github.com/slskd/slskd)** running and accessible
- A valid slskd **API key** (configured in slskd's settings)

## Installation

```bash
pip install git+https://github.com/GeiserX/slskd-transform.git
```

Or for development:

```bash
git clone https://github.com/GeiserX/slskd-transform.git
cd slskd-transform
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set your API key (or put it in config.yml)
export SLSKD_API_KEY="your-api-key-here"

# Search for FLAC versions of all files in ./music
slskd-transform search

# Search recursively in your existing library
slskd-transform search --music-dir /path/to/library --recursive

# Rename downloaded FLACs using metadata
slskd-transform rename --source-dir /path/to/downloads --dest-dir /path/to/organized
```

## Configuration

slskd-transform loads configuration from multiple sources with this priority:

```
CLI flags  >  Environment variables  >  Config file  >  Defaults
```

### Config File

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

### Environment Variables

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

### CLI Reference

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

## Docker

```bash
docker run --rm \
  -e SLSKD_HOST=http://slskd:5030 \
  -e SLSKD_API_KEY=your-key \
  -v /path/to/lossy:/app/music:ro \
  -v /path/to/downloads:/app/downloads \
  ghcr.io/geiserx/slskd-transform:2.0.0 search --recursive
```

Or in a compose stack alongside slskd:

```yaml
services:
  slskd:
    image: slskd/slskd:0.21.4
    ports:
      - "5030:5030"
    volumes:
      - ./slskd-data:/app

  slskd-transform:
    image: ghcr.io/geiserx/slskd-transform:2.0.0
    environment:
      SLSKD_HOST: http://slskd:5030
      SLSKD_API_KEY: your-key
    volumes:
      - /path/to/lossy:/app/music:ro
      - ./slskd-data/downloads:/app/downloads
    command: ["search", "--recursive"]
```

## How It Works

```
Local library          Soulseek network          Your disk
 (lossy files)                                   (FLAC files)

  song.mp3  ──────>  Search "song flac"  ──────>  song.flac
       │                     │                        │
  read duration        compare duration          enqueue if
  with mutagen         (+/- 15 seconds)          match found
       │                     │                        │
       └──── no match ──>  unfound_songs.csv          │
                                                      v
                                         slskd-transform rename
                                          Artist - Title.flac
```

## Related Music Tools

| Project | Description |
|---------|-------------|
| [telegram-slskd-local-bot](https://github.com/GeiserX/telegram-slskd-local-bot) | Automated music discovery and download via Telegram |
| [audio-transcode-watcher](https://github.com/GeiserX/audio-transcode-watcher) | Automated multi-format audio transcoding with lyrics fetching |
| [jellyfin-encoder](https://github.com/GeiserX/jellyfin-encoder) | Automatic 720p HEVC/AV1 transcoding for Jellyfin |

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
