# How it works

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

## Feature details

- **Duration-based matching** -- Compares local track duration against search results with a configurable tolerance (default: 15 seconds).
- **Recursive scanning** -- Point it at your existing music library with `--recursive`, no need to flatten files first.
- **Multi-threaded search** -- Distributes searches across multiple threads (default: 5) for faster processing.
- **Flexible configuration** -- Config file, environment variables, or CLI flags. No code editing required.
- **Automatic enqueue** -- Matched FLAC files are enqueued for download directly through the slskd API.
- **CSV reporting** -- Tracks that could not be found are written to `unfound_songs.csv`.
- **Metadata-based renaming** -- Reads FLAC tags and renames files to `Artist - Title.flac`.
- **Docker support** -- Run alongside slskd in the same compose stack.
