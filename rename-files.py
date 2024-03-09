import os
import shutil
from mutagen.flac import FLAC

def collect_flac_files(directory):
    flac_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.flac'):
                flac_files.append(os.path.join(root, file))
    return flac_files

def extract_metadata(file_path):
    audio = FLAC(file_path)
    title = audio.get('title', ['Unknown'])[0]
    artist = audio.get('artist', ['Unknown'])[0]
    return title, artist

def sanitize_filename(filename):
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename
        
def move_and_rename_flac_files(flac_files, destination):
    for file in flac_files:
        title, artist = extract_metadata(file)
        new_filename = sanitize_filename(f"{artist} - {title}.flac")
        new_filepath = os.path.join(destination, new_filename)

        # Move or rename the .flac file
        shutil.move(file, new_filepath)
        print(f"Moved and renamed: {new_filepath}")

source_directory = 'G:\\slskd\\downloads'
destination_directory = 'G:\\slskd\\'
flac_files = collect_flac_files(source_directory)

move_and_rename_flac_files(flac_files, destination_directory)
