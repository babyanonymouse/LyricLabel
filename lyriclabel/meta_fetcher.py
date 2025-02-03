import requests
import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

# Replace with your own Last.fm API key
LASTFM_API_KEY = "0526879300a394a39f059a5c1975fc01"


def fetch_metadata_from_lastfm(song_name, quiet_mode=False):
    # Search for the song first using the track.search method
    search_url = f"http://ws.audioscrobbler.com/2.0/?method=track.search&track={song_name}&api_key={LASTFM_API_KEY}&format=json"

    try:
        # Make a request to the search API
        search_response = requests.get(search_url)
        search_response.raise_for_status()  # Raise an exception for HTTP errors
        search_data = search_response.json()

        # Check if any tracks were found
        if "results" in search_data and "trackmatches" in search_data["results"]:
            tracks = search_data["results"]["trackmatches"]["track"]
            if tracks:
                # Show the tracks if it's not in quiet mode
                if not quiet_mode:
                    print(f"Found {len(tracks)} result(s) for '{song_name}':\n")
                    for i, track in enumerate(tracks):
                        print(
                            f"{i + 1}. Artist: {track['artist']}, Track: {track['name']}"
                        )

                # Automatically choose the first track if quiet mode is enabled
                if quiet_mode:
                    track = tracks[0]  # Choose the first result
                    # Fetch more detailed metadata about the selected track
                    return fetch_detailed_metadata(track)

                # Otherwise, ask the user to select a track
                choice = int(
                    input("\nPlease select the track number (or 0 to cancel): ")
                )
                if choice == 0:
                    print("Search cancelled.")
                    return None
                elif 1 <= choice <= len(tracks):
                    track = tracks[choice - 1]  # Select the track based on user choice
                    # Fetch more detailed metadata about the selected track
                    return fetch_detailed_metadata(track)
                else:
                    print(
                        f"Invalid choice. Please select a number between 1 and {len(tracks)}."
                    )
                    return None
            else:
                print(f"No matching tracks found for: {song_name}")
                return None
        else:
            print(f"No results found for song: {song_name}")
            return None

    except requests.exceptions.RequestException as e:
        # Handle network errors (e.g., connection issues)
        print(f"Network error occurred: {e}")
        return None
    except ValueError as e:
        # Handle JSON decoding errors
        print(f"Error decoding the response: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return None


def fetch_detailed_metadata(track):
    """Fetch detailed metadata using track.getInfo."""
    track_info_url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={track["artist"]}&track={track["name"]}&api_key={LASTFM_API_KEY}&format=json'
    try:
        # Fetch detailed metadata
        track_info_response = requests.get(track_info_url)
        track_info_response.raise_for_status()  # Raise an exception for HTTP errors
        track_info_data = track_info_response.json()

        if "track" in track_info_data:
            track_details = track_info_data["track"]
            # Safely fetch metadata, providing defaults where necessary
            metadata = {
                "artist": track_details.get("artist", {}).get("name", "Unknown"),
                "album": track_details.get("album", {}).get("title", "Unknown"),
                "track": track_details.get("name", "Unknown"),
                "genre": (
                    "Unknown"
                    if not track_details.get("toptags", {}).get("tag")
                    else track_details.get("toptags", {})
                    .get("tag", [{}])[0]
                    .get("name", "Unknown")
                ),
                "year": track_details.get("release_date", "Unknown")[
                    :4
                ],  # Extracting the year correctly
            }
            return metadata
        else:
            print("Detailed info could not be fetched for the selected track.")
            return None
    except requests.exceptions.RequestException as e:
        # Handle network errors (e.g., connection issues)
        print(f"Error fetching detailed info: {e}")
        return None
    except KeyError as e:
        # Handle missing key errors
        print(f"Missing expected metadata field: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred while fetching detailed info: {e}")
        return None


def extract_artist_and_title(filename):
    """Extract the artist and title from the filename using regex."""
    # Try to extract artist and title using a common format like "Artist - Title.mp3"
    match = re.match(r"^(.*?)\s*[-–]\s*(.*?)(\.mp3)$", filename, re.IGNORECASE)
    if match:
        artist = match.group(1).strip()
        title = match.group(2).strip()
        return artist, title
    else:
        return None, filename.replace(".mp3", "").strip()


def update_metadata(song_path, metadata):
    """Update the metadata of the MP3 file using Mutagen."""
    try:
        # Load the MP3 file and ensure it has ID3 tags
        audio = MP3(song_path, ID3=EasyID3)

        # Update metadata fields
        audio["artist"] = metadata["artist"]
        audio["album"] = metadata["album"]
        audio["title"] = metadata["track"]
        audio["genre"] = metadata["genre"]
        audio["date"] = metadata["year"]

        # Save changes to the file
        audio.save()
        print(f"Metadata updated successfully for '{song_path}'.")

    except Exception as e:
        print(f"Error updating metadata: {e}")


def main():
    # Ask user for song filename
    song_filename = input("Enter the filename of the song (with extension): ")

    if not song_filename.strip():
        print("Error: Filename cannot be empty.")
        return

    # Extract artist and title from the filename
    artist, title = extract_artist_and_title(song_filename)

    if artist and title:
        # If both artist and title are extracted, directly fetch metadata
        print(f"Artist: {artist}, Title: {title}")
        metadata = fetch_metadata_from_lastfm(f"{title} {artist}")
        if metadata:
            update_metadata(song_filename, metadata)
    else:
        # If only title is extracted, prompt the user for multiple results
        print(f"Only the title '{title}' is extracted, prompting for selection...")
        metadata = fetch_metadata_from_lastfm(title)
        if metadata:
            update_metadata(song_filename, metadata)


if __name__ == "__main__":
    main()
