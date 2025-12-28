# Drum Tracker Sorter

This script scans your audio folders, matches files by name, copies metadata from the original track to processed versions, cleans tag noise, and moves files into the correct destination folders.

Supported workflows:

- Match processed tracks against originals
- Copy title / artist / genre / cover art
- Normalize filenames (removes tag suffixes)
- Sort into:
  - `Drumless Tracks`
  - `Isolated Drums`
- Handle metronome versions
- Clean `.sfk` garbage files

---

## Folder Structure

Place this script in a folder containing the directories below:
- `drum-tracker-sorter.py`
- `Original Songs`
- `To Sort`
- `Metronome`
- `BPMs`
- `Drumless Tracks`
- `Isolated Drums`


The script reads from:

- `Original Songs`
- `To Sort`
- `Metronome`
- `BPMs`

and writes sorted files into:

- `Drumless Tracks`
- `Isolated Drums`

---

## How Matching Works

A track is matched by normalized base name:

- Lowercased
- Strips tags like `[drums]`, `[rebalanced]`, etc.
- Removes numeric prefixes
- Removes trailing `"drums"`

Examples that will match as the same song:


