# Usage

`slskd-transform` has two commands: `search` finds a version of each file in your library in the target format (FLAC by default, `--format` to change it) and queues it in slskd, and `rename` files the finished downloads as `Artist - Title.flac` from their tags.

## Examples

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

## Command reference

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

The options listed above the commands (`--config`, `--host`, `--api-key`, `--no-verify-ssl`, `--threads`) go before the command name, and the command's own options after it:

```bash
slskd-transform --api-key your-api-key --threads 3 search --music-dir /path/to/library --recursive
```

Written after `search` or `rename`, they fail with `Error: No such option '--api-key'`.

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

