# Getting started

<p>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/slskd/slskd"><img src="https://img.shields.io/badge/requires-slskd-1A1A2E?style=flat-square" alt="Requires slskd"></a>
</p>

## Prerequisites

- **Python 3.10+**
- **[slskd](https://github.com/slskd/slskd)** running and reachable from this machine
- A valid slskd **API key** (configured in slskd's settings)

## Install

```bash
pip install git+https://github.com/GeiserX/slskd-transform.git
```

To install a given release, add its tag: `pip install git+https://github.com/GeiserX/slskd-transform.git@v2.0.1`. The package is not on PyPI, and there is no published Docker image.

## First run

Point it at your library as it is, folders and all; nothing needs copying into a separate folder first.

```bash
export SLSKD_HOST="http://127.0.0.1:5030"
export SLSKD_API_KEY="your-api-key-here"
slskd-transform search --music-dir /path/to/library --recursive
```

It works when it prints a `Searching for:` line per track and an `Enqueued:` line for each match, and the matches show up in the Downloads page of slskd's web UI. Tracks it could not match are listed in `unfound_songs.csv` in the folder you passed to `--music-dir`. Each search waits 60 seconds for answers, so a large library takes hours; [Configuration](configuration.md) has the settings that change that.

When slskd has finished the downloads, file them by their tags:

```bash
slskd-transform rename --source-dir /path/to/slskd/downloads --dest-dir /path/to/organized
```

What to run next is in [Usage](usage.md).
