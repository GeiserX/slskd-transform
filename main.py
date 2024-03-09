import os
import slskd_api
import time
import mutagen
import requests
import csv
from threading import Thread

def write_unfound_songs_to_csv(unfound_songs, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Song Name'])

        for song in unfound_songs:
            csv_writer.writerow([song])

def list_files_without_ext(music_dir):
    filenames = []
    for file in os.listdir(music_dir):
        if not file.startswith('.'):
            file_without_ext = os.path.splitext(file)[0]
            filenames.append(file_without_ext)
    return filenames

def list_files_with_duration(music_dir):
    filenames = []
    for file in os.listdir(music_dir):
        if not file.startswith('.'):
            file_without_ext = os.path.splitext(file)[0]
            file_path = os.path.join(music_dir, file)
            audio_info = mutagen.File(file_path, easy=True)
            duration = int(audio_info.info.length)
            filenames.append((file_without_ext, duration))
    return filenames

def find_close_duration_song(search_results, local_duration):
    duration_tolerance = 15  # Set the duration tolerance in seconds
    for result in search_results:
        if 'files' in result and len(result['files']) > 0:
            file_info = result['files'][0]
            try:
                result_duration = int(file_info['length'])
                if abs(local_duration - result_duration) <= duration_tolerance:
                    return result
            except KeyError:
                pass
    return None

def remove_hyphens_and_trim(song_name):
    return ' '.join(segment.strip() for segment in song_name.split('-'))

def search_and_enqueue(songs_with_duration, unfound_songs):
    for song_name, local_duration in songs_with_duration:
        song_name_cleaned = remove_hyphens_and_trim(song_name)
        print(f"Searching for: {song_name_cleaned}")

        search_response = slskd.searches.search_text(searchText=(song_name_cleaned + " flac"))

        # Wait a few seconds for search results to populate
        time.sleep(60)

        search_id = search_response['id']
        search_results = slskd.searches.search_responses(id=search_id)

        result = find_close_duration_song(search_results, local_duration)
        if result is not None:
            file_info = result['files'][0]
            print(f"Enqueueing: {file_info['filename']}")
            try:
                success = slskd.transfers.enqueue(username=result['username'], files=[{'filename': file_info['filename'], 'size': file_info['size']}])
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

def threaded_search_and_enqueue(songs_with_duration, unfound_songs, num_threads=5):
    thread_list = []
    chunk_size = len(songs_with_duration) // num_threads

    for i in range(num_threads):
        if i == num_threads - 1:  # last thread takes the remaining songs
            chunk = songs_with_duration[i * chunk_size:]
        else:
            chunk = songs_with_duration[i * chunk_size : (i + 1) * chunk_size]
        thread = Thread(target=search_and_enqueue, args=(chunk, unfound_songs))
        thread.start()
        thread_list.append(thread)
        time.sleep(10)

    for thread in thread_list:
        thread.join()

slskd = slskd_api.SlskdClient(host="http://127.0.0.1:5030", api_key="...", verify_ssl=False)

current_dir = os.getcwd()
MUSIC_DIR = os.path.join(current_dir, 'music')
songs_with_duration = list_files_with_duration(MUSIC_DIR)

unfound_songs = []

threaded_search_and_enqueue(songs_with_duration, unfound_songs)

if len(unfound_songs) > 0:
    write_unfound_songs_to_csv(unfound_songs, 'unfound_songs.csv')
    print("Unfound songs have been written to 'unfound_songs.csv'")
