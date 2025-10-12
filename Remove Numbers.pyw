import os
import re

DIR = "Isolated Drums"

def remove_leading_numbers_from_mp3_filenames():
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    drumless_dir = os.path.join(script_dir, DIR)

    # Iterate over all items in Drumless Tracks
    for item in os.listdir(drumless_dir):
        path = os.path.join(drumless_dir, item)

        # Process MP3 files directly in Drumless Tracks
        if os.path.isfile(path) and path.lower().endswith(".mp3"):
            process_file(path)

        # Process MP3 files in immediate subfolders (but not deeper)
        elif os.path.isdir(path):
            for file in os.listdir(path):
                if file.lower().endswith(".mp3"):
                    process_file(os.path.join(path, file))

def process_file(file_path):
    """Removes leading numeric prefix from a single MP3 file name if present."""
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    parts = name.split(" ", 1)
    if len(parts) > 1 and re.fullmatch(r"\d+", parts[0]):
        new_name = parts[1].strip() + ext
        new_path = os.path.join(folder, new_name)

        if new_name != filename:
            os.rename(file_path, new_path)
            print(f"Renamed: {filename} → {new_name}")
    else:
        print(f"Skipped: {filename}")

if __name__ == "__main__":
    remove_leading_numbers_from_mp3_filenames()
