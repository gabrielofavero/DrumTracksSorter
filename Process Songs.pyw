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

last_track_number = 0

#######################
## Support Functions ##
#######################

# Function to get the type of the file (Isolated Drums or Drumless Tracks)
def get_type(text):
    if '[drums]' in text:
        return "Isolated Drums"
    elif '[rebalanced]' in text:
        return "Drumless Tracks"
    elif '[bass music vocals]' in text:
        return "Drumless Tracks"
    else:
        return ""

# Function to extract track number from file name
def get_track_number(filename):
    spaceSplit = filename.split(" ")[0]
    if spaceSplit.isdigit():
        return spaceSplit
    else:
        formatSplit = filename.split(".")[0]
        if formatSplit.isdigit():
            return formatSplit
    return None

# Function to get file and path by track number                              
def get_file_and_path_by_track_number(track_number, dir):
    for file in os.listdir(dir):
        if file.endswith(".mp3"):
            if get_track_number(file) == track_number:
                print(f'File with track number "{track_number}" found as "{file}" in "{dir}".')
                return file, os.path.join(dir, file)
    return None, None        
  
# Function to get song metadata from an MP3 file
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

# Function to update metadata for an MP3 file
def update_mp3_metadata(file_path, title, artist, genre, cover, track_number, album):
    audio = MP3(file_path, ID3=ID3)
    
    # print(f'All tags with values: {audio.pprint()}')

    # Ensure the file has tags or create them
    if audio.tags is None:
        audio.add_tags()

    # Remove existing tags before updating them to avoid conflicts
    if 'TIT2' in audio.tags:
        del audio.tags['TIT2']  # Delete the title tag
    if 'TPE1' in audio.tags:
        del audio.tags['TPE1']  # Delete the artist tag
    if 'TPE2' in audio.tags:
        del audio.tags['TPE2']  # Delete the album artist tag
    if 'TRCK' in audio.tags:
        del audio.tags['TRCK']  # Delete the track number tag
    if 'TCON' in audio.tags:
        del audio.tags['TCON']  # Delete the genre tag
    if 'TALB' in audio.tags:
        del audio.tags['TALB'] # Delete the album tag
        
    audio.tags.delall('TXXX')  # Delete all TXXX tags (including comment)

    # Update metadata fields correctly as lists of strings
    audio.tags['TIT2'] = mutagen.id3.TIT2(encoding=3, text=[title])  # Title
    audio.tags['TPE1'] = mutagen.id3.TPE1(encoding=3, text=[artist])  # Artist
    audio.tags['TPE2'] = mutagen.id3.TPE2(encoding=3, text=["Various Artists"])  # Album Artist
    audio.tags['TRCK'] = mutagen.id3.TRCK(encoding=3, text=[track_number])  # Track number
    audio.tags['TCON'] = mutagen.id3.TCON(encoding=3, text=[genre])  # Genre
    audio.tags['TALB'] = mutagen.id3.TALB(encoding=3, text=[album])  # Album

    # Add cover image if available
    if cover:
        # Remove existing album cover if it exists
        audio.tags.delall('APIC')
        audio.tags.add(
            APIC(
                encoding=3, 
                mime='image/jpeg',  # or 'image/png'
                type=3,  # Album cover type
                desc='Cover',
                data=cover
            )
        )

    # Save the updated metadata to the file
    audio.save()

def strip_extra_tags(file_name):
    tags = ["[drums]", "[rebalanced]", "[bass music vocals]"]

    for tag in tags:
        file_name = file_name.replace(f" {tag}", "").replace(tag, "").strip()

    return file_name

# Function to rename and move a file
def rename_and_move_file(old_name, new_name, file_type, old_dir, override=False):    
    old_file_path = os.path.join(old_dir, old_name)
    
    if file_type == "Isolated Drums":
        new_file_path = os.path.join(isolated_drums_dir, new_name)
    elif file_type == "Drumless Tracks":
        new_file_path = os.path.join(drumless_tracks_dir, new_name)
    else:
        new_file_path = os.path.join(old_dir, new_name)
        
    # Check if the file already exists in the destination directory. If so, confirm with y/n
    if os.path.exists(new_file_path):
        if override:
            remove_file(new_file_path, new_name, file_type)
        else:
            print(f'File "{new_name}" already exists in "{file_type}" directory. Do you want to overwrite it? (y/n/yall)')
            choice = input().lower()
            if choice == 'y':
                remove_file(new_file_path, new_name, file_type)
            elif choice == 'yall':
                remove_file(new_file_path, new_name, file_type)
                override = True
            else:
                os.rename(old_file_path, os.path.join(old_dir, new_name))
                print(f'Renamed: "{old_name}" to "{new_name}". File not moved.')
                return

    
    os.rename(old_file_path, new_file_path)
    print(f'Renamed: "{old_name}" to "{new_name}"')
    
    if new_file_path != old_file_path:
        print(f'Moved: "{new_name}" to "{file_type}"')
    
    return override

def remove_file(file_path, file_name, file_type):
    os.remove(file_path)
    if file_name and file_type:
        print(f'Removed: "{file_name}" from "{file_type}"')
    else:
        print(f'Removed: "{file_name}"')

####################
## Main Functions ##
####################

# Function to clean .sfk files in a directory        
def clean_sfk_files(dir):
    print(f"Started cleaning .sfk files in '{dir}' directory")
    
    if not os.path.exists(dir):
        print(f"Directory {dir} not found.")
        print()
        return
    
    found_files = False
    
    for file in os.listdir(dir):
        if file.endswith(".sfk"):
            found_files = True
            file_path = os.path.join(dir, file)
            os.remove(file_path)
            print(f'Removed: "{file}" from "{dir}"')
    
    if not found_files:
        print(f"No .sfk files found in '{dir}' directory")
    
    print()

# Function to process files in Temp directories
def process_to_sort_dir():
    print(f"Started processing files in 'Temp - To Sort' directory")
    
    # Check if the directories exists
    if not os.path.exists(original_songs_dir):
        print(f"Directory {original_songs_dir} not found.")
        print()
        return
    if not os.path.exists(to_sort_dir):
        print(f"Directory {to_sort_dir} not found.")
        print()
        return
    
    # Check if the directories are empty
    if not os.listdir(original_songs_dir):
        print(f'"Temp - Original Songs" directory is empty. Skipping operation.')
        print()
        return
    if not os.listdir(to_sort_dir):
        print(f'"Temp - To Sort" directory is empty. Skipping operation.')
        print()
        return
    
    # Loop over files in Temp directory
    override = False
    for original_song in os.listdir(original_songs_dir):
        if original_song.endswith(".mp3"):
            original_song_path = os.path.join(original_songs_dir, original_song)

            # Extract song metadata from the file in Temp
            song_name, song_artist, song_genre, song_cover = get_mp3_metadata(original_song_path)
            track_number = get_track_number(original_song)

            # Search corresponding files in "Temp - To Sort"
            
            for sort_file in os.listdir(to_sort_dir):
                if sort_file.endswith(".mp3"):
                    print (f"Sort File: {sort_file}")
                    sort_file_clean = strip_extra_tags(sort_file)
                    print (f"Sort File Clean: {sort_file_clean}")
                    sort_file_type = get_type(sort_file)

                    # Check if the name matches (ignoring extra tags)
                    if original_song.replace(".mp3", "").lower() == sort_file_clean.replace(".mp3", "").lower():
                        sort_file_path = os.path.join(to_sort_dir, sort_file)

                        # Update metadata in "Temp - To Sort"
                        update_mp3_metadata(sort_file_path, song_name, song_artist, song_genre, song_cover, track_number, sort_file_type)

                        # Log metadata update
        
                        if song_cover:
                            print(f'Song Metadata of "{sort_file}" updated with song name "{song_name}", artist "{song_artist}", track number "{track_number}", and album cover.')
                        else:
                            print(f'Song Metadata of "{sort_file}" updated with song name "{song_name}", artist "{song_artist}", and track number "{track_number}".')
                        override = rename_and_move_file(sort_file, sort_file_clean, sort_file_type, to_sort_dir, override)
                        
            print()

# Function to process files in "Temp - Metronome" directory
def process_metronome_dir():
    print(f"Started processing files in 'Temp - Metronome' directory")
    
    # Check if the directory exists
    if not os.path.exists(metronome_dir):
        print(f"Directory {metronome_dir} not found.")
        print()
        return
    
        # Check if the directory exists
    if not os.path.exists(original_songs_dir):
        print(f"Directory {original_songs_dir} not found.")
        print()
        return
    
    override = False
    for metronome_file in os.listdir(metronome_dir):
        if metronome_file.endswith(".mp3"):
            track_number = get_track_number(metronome_file)
            print()
            print(f"Processing metronome file {metronome_file} with track number {track_number}")
            track_path = os.path.join(metronome_dir, metronome_file)
            type = "Drumless Tracks"
            if "drums" in metronome_file:
                type = "Isolated Drums"
            
            corresponding_file = None
            corresponding_path = None
            
            search_dirs = [original_songs_dir, drumless_tracks_dir, isolated_drums_dir]
            for dir in search_dirs:
                corresponding_file, corresponding_path = get_file_and_path_by_track_number(track_number, dir)
                if corresponding_file:
                    break
            
            if not corresponding_file:
                print(f"Corresponding file for metronome file {metronome_file} not found. Skipping.")
                continue
            
            # Extract song metadata from the corresponding file
            song_name, song_artist, song_genre, song_cover = get_mp3_metadata(corresponding_path)
            
            # Update metadata in "Temp - Metronome"
            update_mp3_metadata(track_path, song_name, song_artist, song_genre, song_cover, track_number, type)
            print(f'Metronome file "{metronome_file}" updated with song name "{song_name}", artist "{song_artist}", track number "{track_number}", and album cover.')
            
            # Move the file to the appropriate directory
            override = rename_and_move_file(metronome_file, corresponding_file, type, metronome_dir, override)
            
    print()
         
# Main function to process songs    
def process_songs():
    print()
    
    clean_sfk_files(drumless_tracks_dir)
    clean_sfk_files(isolated_drums_dir)
    clean_sfk_files(to_sort_dir)
    clean_sfk_files(bpm_dir)
    
    process_to_sort_dir()
    process_metronome_dir()
    
    print(f"Finished processing songs.")
    print()

process_songs()