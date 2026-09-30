# Troubleshooting

## Error: No such option '--api-key'

`--api-key`, `--host`, `--config`, `--no-verify-ssl` and `--threads` belong to `slskd-transform` itself, so they go before the command name:

```bash
slskd-transform --api-key your-api-key search --music-dir /path/to/library --recursive
```

Written after `search` or `rename`, they are rejected. `--music-dir`, `--recursive`, `--format`, `--tolerance` and `--timeout` go after `search`. See [Usage](usage.md#command-reference).

## Error: No API key configured

No key was found in a flag, in `SLSKD_API_KEY` or in a config file. When you put it in `config.yml`, check two things:

- The file is where the tool looks: the directory you run the command from, or `~/.config/slskd-transform/config.yml`, or the path you pass with `--config`. A `config.yml` anywhere else, for example in the folder you cloned the code into, is read only when you run the command from that folder.
- The key is spelled `api_key` (and the address `host`). Other names, such as `slskd_api_key` or `slskd_url`, are ignored without a warning. [Configuration](configuration.md#config-file) shows every valid key.

## Error: Invalid value for '--music-dir'

The folder does not exist as typed. Put a path with spaces in quotes: `--music-dir "/path/to/My Music"`. On Windows the same applies: `--music-dir "D:\Music\My Library"`.

## It prints nothing and exits

No audio file was found at the top of `--music-dir`. When your music sits in artist or album folders, add `--recursive`.

## A traceback ending in ConnectionError or HTTPError 401

The search could not reach slskd (`ConnectionError`: wrong `host`, slskd not running, or a firewall in between) or slskd refused the API key (`401 Client Error: Unauthorized`). Check that `host` opens slskd's web UI from the same machine, and that the key matches one in slskd's settings. The command still exits with status 0 in this case and no `unfound_songs.csv` is written for the tracks it did not reach, so do not rely on the exit status in a script.

## The scan stopped on a damaged file

Before 2.0.1, one audio file with broken tags (for example an `.m4a` with damaged chapter data) stopped the whole scan with a `mutagen` error. Upgrade:

```bash
pip install --upgrade git+https://github.com/GeiserX/slskd-transform.git
```

From 2.0.1 on, such a file is skipped and never searched. To include it, rewrite its container without re-encoding the audio, `ffmpeg -i broken.m4a -c copy fixed.m4a`, and run `search` again.

## A track you know is on Soulseek ends up in unfound_songs.csv

- The search text is the file name. A file named `01 Track 01.mp3` searches for exactly that; rename it `Artist - Title.mp3` first.
- The copies found differ in length by more than 15 seconds, which is normal for a live or remastered version. Raise `--tolerance` if you accept those.
- The answers arrived after `--timeout` seconds. Raise it on a slow connection.
- Only the first file of each peer's answer is compared, so a peer that has the right file further down its list is missed. See [How it works](how-it-works.md#what-search-does-step-by-step).

## It takes hours

Each search waits `--timeout` seconds (60 by default) and each thread runs one search at a time, so 1,000 tracks at the defaults take more than three hours. `--threads` runs more searches side by side; a lower `--timeout` finishes sooner but collects fewer answers.

## Reporting a bug

Open an [issue](https://github.com/GeiserX/slskd-transform/issues) with:

- the version (`pip show slskd-transform`), your operating system and `python --version`;
- your slskd version;
- the exact command and its full output, traceback included;
- for a missed track, its file name and length, and what you expected it to match.

Never paste your API key; replace it with `***`.
