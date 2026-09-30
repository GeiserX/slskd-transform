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

## What search does, step by step

1. It lists the audio files in `--music-dir`, the top level only unless `--recursive` is set, and skips hidden files. It reads each file's length with [mutagen](https://github.com/quodlibet/mutagen); a file mutagen cannot read is skipped and never searched. Files that are already FLAC are searched like any other.
2. It splits the list across `--threads` searches (5 by default) and starts them 10 seconds apart.
3. For each track it sends slskd the file name without its extension, with hyphens turned into spaces, plus the target format: `Demo Band - Slow Tide.mp3` becomes the search `Demo Band Slow Tide flac`.
4. It waits `search_timeout` seconds (60 by default), then reads slskd's answers. From each peer's answer it looks at the first file only, and queues the first one whose length is within `duration_tolerance` seconds (15 by default) of your track.
5. A track with no match, or one slskd refused to queue, goes into `unfound_songs.csv` at the top of `--music-dir`. A run that leaves any track unmatched overwrites the file; a run that matches every track leaves the old one in place.

## What rename does

It walks `--source-dir` and every folder under it, takes each `.flac` file, reads its `artist` and `title` tags (`Unknown` when a tag is missing), removes the characters `\ / : * ? " < > |`, and moves the file into `--dest-dir` as `Artist - Title.flac`. A file of the same name already there is replaced.

## Feature details

- **Duration-based matching** -- Compares local track duration against search results with a configurable tolerance (default: 15 seconds).
- **Recursive scanning** -- Point it at your existing music library with `--recursive`, no need to flatten files first.
- **Multi-threaded search** -- Distributes searches across multiple threads (default: 5) for faster processing.
- **Flexible configuration** -- Config file, environment variables, or CLI flags. No code editing required.
- **Automatic enqueue** -- Matched FLAC files are enqueued for download directly through the slskd API.
- **CSV reporting** -- Tracks that could not be found are written to `unfound_songs.csv`.
- **Metadata-based renaming** -- Reads FLAC tags and renames files to `Artist - Title.flac`.
