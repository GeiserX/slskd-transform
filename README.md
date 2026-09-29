<p align="center">
  <img src="docs/images/banner.svg" alt="slskd-transform banner" width="900"/>
</p>

<p align="center">
  <strong>Bulk-upgrade your music library from lossy to lossless via Soulseek</strong>
</p>

<p align="center">
  <a href="https://github.com/GeiserX/slskd-transform/releases"><img src="https://img.shields.io/github/v/release/GeiserX/slskd-transform?style=flat-square" alt="Release"></a>
  <a href="https://github.com/GeiserX/slskd-transform/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/GeiserX/slskd-transform/tests.yml?style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/GeiserX/slskd-transform/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GeiserX/slskd-transform?style=flat-square&color=FF6F00" alt="License"></a>
  <a href="https://github.com/GeiserX/slskd-transform/stargazers"><img src="https://img.shields.io/github/stars/GeiserX/slskd-transform?style=flat-square&color=FFD54F" alt="Stars"></a>
  <a href="https://codecov.io/gh/GeiserX/slskd-transform"><img src="https://img.shields.io/codecov/c/github/GeiserX/slskd-transform?style=flat-square" alt="Coverage"></a>
</p>

**slskd-transform** scans your local music library, searches the [Soulseek](https://www.slsknet.org/) network through [slskd](https://github.com/slskd/slskd) for matching FLAC versions of each track, and automatically enqueues them for download. It matches songs by **audio duration** rather than filenames alone, ensuring you get the correct track every time.

## Features

- Matches tracks by audio duration, within 15 seconds by default, not by file name alone.
- Scans an existing library recursively with `--recursive`.
- Runs searches on several threads (5 by default).
- Enqueues matched FLACs straight through the slskd API.
- Writes tracks it could not find to `unfound_songs.csv`.
- Renames downloads to `Artist - Title.flac` from their FLAC tags.
- Takes settings from a config file, `SLSKD_` environment variables or CLI flags.
- Runs in Docker next to slskd.

## Quick start

```bash
pip install git+https://github.com/GeiserX/slskd-transform.git
export SLSKD_API_KEY="your-api-key-here"
slskd-transform search --music-dir /path/to/library --recursive
```

Then `slskd-transform rename --source-dir /path/to/downloads --dest-dir /path/to/organized` once the downloads land.

## Documentation

- [Installation](docs/installation.md): prerequisites, pip, development setup, Docker and compose, usage examples
- [Configuration](docs/configuration.md): config file, environment variables, CLI reference
- [How it works](docs/how-it-works.md): the search and rename flow, feature details

## Related music tools

| Project | Description |
|---------|-------------|
| [telegram-slskd-local-bot](https://github.com/GeiserX/telegram-slskd-local-bot) | Automated music discovery and download via Telegram |
| [audio-transcode-watcher](https://github.com/GeiserX/audio-transcode-watcher) | Automated multi-format audio transcoding with lyrics fetching |
| [quality-gate-encoder](https://github.com/GeiserX/quality-gate-encoder) (formerly jellyfin-encoder) | Automatic 720p HEVC/AV1 transcoding for Jellyfin |

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
