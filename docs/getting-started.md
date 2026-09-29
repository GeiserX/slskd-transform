# Getting started

<p>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/slskd/slskd"><img src="https://img.shields.io/badge/requires-slskd-1A1A2E?style=flat-square" alt="Requires slskd"></a>
</p>

## Prerequisites

- **Python 3.10+**
- **[slskd](https://github.com/slskd/slskd)** running and accessible
- A valid slskd **API key** (configured in slskd's settings)

## Install

```bash
pip install git+https://github.com/GeiserX/slskd-transform.git
```

Or for development:

```bash
git clone https://github.com/GeiserX/slskd-transform.git
cd slskd-transform
pip install -e ".[dev]"
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

What to run next is in [Usage](usage.md).
