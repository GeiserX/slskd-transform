"""Search and enqueue module for slskd-transform."""

from __future__ import annotations

import os
import time
from threading import Thread

import mutagen
import requests
import slskd_api

from slskd_transform.config import SlskdConfig
from slskd_transform.utils import write_unfound_songs_to_csv


def list_files_with_duration(
    music_dir: str,
    *,
    recursive: bool = False,
    format_filter: str | None = None,
) -> list[tuple[str, int]]:
    """Scan a directory for audio files and return (filename_without_ext, duration) tuples."""
    filenames: list[tuple[str, int]] = []

    if recursive:
        for root, _dirs, files in os.walk(music_dir):
            for file in files:
                if file.startswith('.'):
                    continue
                file_without_ext = os.path.splitext(file)[0]
                file_path = os.path.join(root, file)
                audio_info = mutagen.File(file_path, easy=True)
                duration = int(audio_info.info.length)
                filenames.append((file_without_ext, duration))
    else:
        for file in os.listdir(music_dir):
            if file.startswith('.'):
                continue
            file_path = os.path.join(music_dir, file)
            if not os.path.isfile(file_path):
                continue
            file_without_ext = os.path.splitext(file)[0]
            audio_info = mutagen.File(file_path, easy=True)
            duration = int(audio_info.info.length)
            filenames.append((file_without_ext, duration))

    return filenames


def find_close_duration_song(
    search_results: list[dict],
    local_duration: int,
    *,
    tolerance: int = 15,
) -> dict | None:
    """Return the first search result whose duration is within tolerance of local_duration."""
    for result in search_results:
        if 'files' in result and len(result['files']) > 0:
            file_info = result['files'][0]
            try:
                result_duration = int(file_info['length'])
                if abs(local_duration - result_duration) <= tolerance:
                    return result
            except KeyError:
                pass
    return None


def remove_hyphens_and_trim(song_name: str) -> str:
    """Split on hyphens, strip each segment, and rejoin with spaces."""
    return ' '.join(segment.strip() for segment in song_name.split('-'))


def search_and_enqueue(
    songs_with_duration: list[tuple[str, int]],
    unfound_songs: list[str],
    *,
    config: SlskdConfig,
    client: slskd_api.SlskdClient,
) -> None:
    """Search slskd for each song and enqueue matching results."""
    for song_name, local_duration in songs_with_duration:
        song_name_cleaned = remove_hyphens_and_trim(song_name)
        print(f"Searching for: {song_name_cleaned}")

        search_response = client.searches.search_text(
            searchText=(song_name_cleaned + " " + config.format)
        )

        time.sleep(config.search_timeout)

        search_id = search_response['id']
        search_results = client.searches.search_responses(id=search_id)

        result = find_close_duration_song(
            search_results, local_duration, tolerance=config.duration_tolerance
        )
        if result is not None:
            file_info = result['files'][0]
            print(f"Enqueueing: {file_info['filename']}")
            try:
                success = client.transfers.enqueue(
                    username=result['username'],
                    files=[{'filename': file_info['filename'], 'size': file_info['size']}],
                )
                if success:
                    print(f"Enqueued: {file_info['filename']}")
                else:
                    print(f"Failed to enqueue: {file_info['filename']}")
                    unfound_songs.append(song_name)
            except requests.exceptions.HTTPError as http_error:
                print(f"Error while sending request to slskd: {http_error}")
                unfound_songs.append(song_name)
        else:
            print(f"Failed to find matching song with close duration for: {song_name}")
            unfound_songs.append(song_name)


def threaded_search_and_enqueue(
    songs_with_duration: list[tuple[str, int]],
    unfound_songs: list[str],
    *,
    config: SlskdConfig,
    client: slskd_api.SlskdClient,
) -> None:
    """Split songs into chunks and search/enqueue in parallel threads."""
    num_threads = config.num_threads
    thread_list: list[Thread] = []
    chunk_size = len(songs_with_duration) // num_threads

    for i in range(num_threads):
        if i == num_threads - 1:
            chunk = songs_with_duration[i * chunk_size:]
        else:
            chunk = songs_with_duration[i * chunk_size : (i + 1) * chunk_size]
        thread = Thread(
            target=search_and_enqueue,
            args=(chunk, unfound_songs),
            kwargs={"config": config, "client": client},
        )
        thread.start()
        thread_list.append(thread)
        time.sleep(10)

    for thread in thread_list:
        thread.join()


def run_search(config: SlskdConfig) -> None:
    """Top-level orchestrator: create client, scan directory, search, and write CSV."""
    client = slskd_api.SlskdClient(
        host=config.host,
        api_key=config.api_key,
        verify_ssl=config.verify_ssl,
    )

    songs_with_duration = list_files_with_duration(
        str(config.music_dir),
        recursive=config.recursive,
    )

    unfound_songs: list[str] = []

    threaded_search_and_enqueue(
        songs_with_duration,
        unfound_songs,
        config=config,
        client=client,
    )

    if len(unfound_songs) > 0:
        write_unfound_songs_to_csv(unfound_songs, config.music_dir / 'unfound_songs.csv')
        print("Unfound songs have been written to 'unfound_songs.csv'")
