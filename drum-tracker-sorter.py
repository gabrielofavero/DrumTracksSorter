import os
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
original_songs_dir = os.path.join(current_dir, 'Temp - Original Songs')
to_sort_dir = os.path.join(current_dir, 'Temp - To Sort')
metronome_dir = os.path.join(current_dir, 'Temp - Metronome')
bpm_dir = os.path.join(current_dir, 'Temp - BPMs')

drumless_tracks_dir = os.path.join(current_dir, 'Drumless Tracks')
isolated_drums_dir = os.path.join(current_dir, 'Isolated Drums')

#######################
## Support Functions ##
#######################

def get_type(text):
    if '[drums]' in text:
        return "Isolated Drums"
    elif '[rebalanced]' in text:
        return "Drumless Tracks"
    elif '[bass music vocals]' in text:
        return "Drumless Tracks"
    else:
        return ""

def get_mp3_metadata(file_path):
    audio = MP3(file_path, ID3=ID3)
    
    title = audio.get('TIT2', 'Unknown Title')
    artist = audio.get('TPE1', 'Unknown Artist')
    genre = audio.get('TCON', 'Other')

    cover = None
    for tag in audio.tags.values():
        if isinstance(tag, APIC):
            cover = tag.data
            break

    return title, artist, genre, cover

def update_mp3_metadata(file_path, title, artist, genre, cover, album):
    audio = MP3(file_path, ID3=ID3)

    if audio.tags is None:
        audio.add_tags()

    # Remove existing tags before updating them
    for tag in ['TIT2', 'TPE1', 'TPE2', 'TRCK', 'TCON', 'TALB']:
        if tag in audio.tags:
            del audio.tags[tag]
    audio.tags.delall('TXXX')  # remove comment-type tags

    # Update metadata
    audio.tags['TIT2'] = mutagen.id3.TIT2(encoding=3, text=[title])
    audio.tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=[artist])
    audio.tags['TCON'] = mutagen.id3.TCON(encoding=3, text=[genre])
    audio.tags['TALB'] = mutagen.id3.TALB(encoding=3, text=[album])

    # Do NOT add TPE2 (album artist)
    # Do NOT add TRCK (track number)

    # Add cover if present
    if cover:
        audio.tags.delall('APIC')
        audio.tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=cover
            )
        )

    audio.save()

def strip_extra_tags(file_name):
    tags = ["[drums]", "[rebalanced]", "[bass music vocals]"]
    for tag in tags:
        file_name = file_name.replace(f" {tag}", "").replace(tag, "").strip()
    return file_name

import re

def normalize_name(name):
    base = os.path.splitext(name)[0]
    base = re.sub(r'\s*\[.*?\]\s*', '', base)
    base = base.strip().lower()
    base = re.sub(r'\s+', ' ', base)
    return base

def rename_and_move_file(old_name, new_name, file_type, old_dir, override=False):    
    old_file_path = os.path.join(old_dir, old_name)
    
    if file_type == "Isolated Drums":
        new_file_path = os.path.join(isolated_drums_dir, new_name)
    elif file_type == "Drumless Tracks":
        new_file_path = os.path.join(drumless_tracks_dir, new_name)
    else:
        new_file_path = os.path.join(old_dir, new_name)
        
    if os.path.exists(new_file_path):
        if override:
            remove_file(new_file_path, new_name, file_type)
        else:
            print(f'File "{new_name}" already exists in "{file_type}" directory. Overwrite? (y/n/yall)')
            choice = input().lower()
            if choice == 'y':
                remove_file(new_file_path, new_name, file_type)
            elif choice == 'yall':
                remove_file(new_file_path, new_name, file_type)
                override = True
            else:
                os.rename(old_file_path, os.path.join(old_dir, new_name))
                print(f'Renamed: "{old_name}" → "{new_name}" (not moved)')
                return

    os.rename(old_file_path, new_file_path)
    print(f'Renamed: "{old_name}" → "{new_name}"')
    if new_file_path != old_file_path:
        print(f'Moved: "{new_name}" to "{file_type}"')

    return override

def remove_file(file_path, file_name, file_type):
    os.remove(file_path)
    print(f'Removed: "{file_name}" from "{file_type}"')

def extract_base_name(filename: str) -> str:
    name = filename.lower().replace(".mp3", "").strip()

    # Remove leading prefix numbers (e.g. "001 Song", "12 Song", etc)
    parts = name.split(" ", 1)
    if parts[0].isdigit() and len(parts) > 1:
        name = parts[1]

    # Remove trailing "drums"
    if name.endswith(" drums"):
        name = name[:-6]  # remove " drums"

    return name.strip().lower()

####################
## Main Functions ##
####################

def clean_sfk_files(dir):
    print(f"Cleaning .sfk files in '{dir}'")
    if not os.path.exists(dir):
        print(f"Directory not found: {dir}\n")
        return

    found = False
    for file in os.listdir(dir):
        if file.endswith(".sfk"):
            os.remove(os.path.join(dir, file))
            print(f"Removed: {file}")
            found = True
    if not found:
        print("No .sfk files found\n")

def process_to_sort_dir():
    print("Processing 'Temp - To Sort' directory...")
    
    if not os.listdir(original_songs_dir) or not os.listdir(to_sort_dir):
        print("One of the Temp directories is empty. Skipping.\n")
        return
    if not os.path.exists(original_songs_dir) or not os.path.exists(to_sort_dir):
        print("One of the required directories was not found.\n")
        return
    if not os.listdir(original_songs_dir) or not os.listdir(to_sort_dir):
        print("One of the Temp directories is empty. Skipping.\n")
        return

    override = False
    for original_song in os.listdir(original_songs_dir):
        if original_song.lower().endswith(('.mp3', '.flac')):
            original_song_path = os.path.join(original_songs_dir, original_song)

            # Choose metadata reader based on file type
            if original_song.lower().endswith('.flac'):
                from mutagen.flac import FLAC
                audio = FLAC(original_song_path)
                song_name = audio.get('title', ['Unknown Title'])[0]
                song_artist = audio.get('artist', ['Unknown Artist'])[0]
                song_genre = audio.get('genre', ['Other'])[0]

                # Extract FLAC cover art (if any)
                song_cover = None
                if audio.pictures:
                    song_cover = audio.pictures[0].data
            else:
                song_name, song_artist, song_genre, song_cover = get_mp3_metadata(original_song_path)

            for sort_file in os.listdir(to_sort_dir):
                if sort_file.endswith(".mp3"):
                    print(f"Sort File: {sort_file}")
                    sort_file_clean = strip_extra_tags(sort_file)
                    print(f"Sort File Clean: {sort_file_clean}")
                    sort_file_type = get_type(sort_file)

                    if normalize_name(original_song) == normalize_name(sort_file):
                        sort_file_path = os.path.join(to_sort_dir, sort_file)
                        update_mp3_metadata(sort_file_path, song_name, song_artist, song_genre, song_cover, sort_file_type)

                        if song_cover:
                            print(f'Metadata updated for "{sort_file}" (cover included)')
                        else:
                            print(f'Metadata updated for "{sort_file}"')
                        override = rename_and_move_file(sort_file, sort_file_clean, sort_file_type, to_sort_dir, override)
            print()

def process_metronome_dir():
    print("Processing 'Temp - Metronome' directory...")
    
    if not os.path.exists(metronome_dir) or not os.path.exists(original_songs_dir):
        print("One of the required directories was not found.\n")
        return

    override = False

    for metronome_file in os.listdir(metronome_dir):
        if metronome_file.endswith(".mp3"):
            print(f"\nProcessing {metronome_file}")

            # Detect type
            type = "Drumless Tracks"
            if "drums" in metronome_file.lower():
                type = "Isolated Drums"

            # Extract clean base name from metronome file
            base_name = extract_base_name(metronome_file)

            # Try to find a matching song
            match = None
            for dir in [original_songs_dir, drumless_tracks_dir, isolated_drums_dir]:
                for file in os.listdir(dir):
                    # extract comparable names from files in dir
                    if extract_base_name(file) == base_name:
                        match = os.path.join(dir, file)
                        break
                if match:
                    break

            if not match:
                print(f"No matching song found for {metronome_file}. Skipping.")
                continue

            # Read metadata from matched song
            song_name, song_artist, song_genre, song_cover = get_mp3_metadata(match)
            track_path = os.path.join(metronome_dir, metronome_file)

            # Update metadata in metronome version
            update_mp3_metadata(track_path, song_name, song_artist, song_genre, song_cover, type)
            print(f'Metadata updated for "{metronome_file}"')

            # Rename + move final file
            override = rename_and_move_file(
                metronome_file,
                os.path.basename(match),
                type,
                metronome_dir,
                override
            )

    print()

def process_songs():
    print()
    clean_sfk_files(drumless_tracks_dir)
    clean_sfk_files(isolated_drums_dir)
    clean_sfk_files(to_sort_dir)
    clean_sfk_files(bpm_dir)
    process_to_sort_dir()
    process_metronome_dir()
    print("Finished processing songs.\n")

if __name__ == "__main__":
    process_songs()
