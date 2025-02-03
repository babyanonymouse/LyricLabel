import requests
import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from dotenv import load_dotenv
load_dotenv()

# Replace with your own Last.fm API key
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


def fetch_metadata_from_lastfm(
    song_name, quiet_mode=False, filename=None, error_list=None
):
    print(f"Searching for song: {song_name}")  # Debugging line

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
                if not quiet_mode:
                    print(f"Found {len(tracks)} result(s) for '{song_name}':\n")
                    for i, track in enumerate(tracks):
                        print(
                            f"{i + 1}. Artist: {track['artist']}, Track: {track['name']}"
                        )

                if quiet_mode:
                    track = tracks[0]  # Choose the first result
                    return fetch_detailed_metadata(track, filename, error_list)

                choice = int(
                    input("\nPlease select the track number (or 0 to cancel): ")
                )
                if choice == 0:
                    error_list.append(f"Search cancelled for '{song_name}'.")
                    return None
                elif 1 <= choice <= len(tracks):
                    track = tracks[choice - 1]
                    return fetch_detailed_metadata(track, filename, error_list)
                else:
                    error_list.append(f"Invalid choice for '{song_name}'.")
                    return None
            else:
                error_list.append(f"No matching tracks found for '{song_name}'.")
                return None
        else:
            error_list.append(f"No results found for song: '{song_name}'.")
            return None

    except requests.exceptions.RequestException as e:
        error_list.append(f"Network error occurred for '{song_name}': {e}")
        return None
    except ValueError as e:
        error_list.append(f"Error decoding the response for '{song_name}': {e}")
        return None
    except Exception as e:
        error_list.append(f"An unexpected error occurred for '{song_name}': {e}")
        return None


def fetch_detailed_metadata(track, filename=None, error_list=None):
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
            error_list.append(f"Detailed info could not be fetched for {filename}")
            return None
    except requests.exceptions.RequestException as e:
        error_list.append(f"Error fetching detailed info for '{filename}': {e}")
        return None
    except KeyError as e:
        error_list.append(f"Missing expected metadata field for '{filename}': {e}")
        return None
    except Exception as e:
        error_list.append(
            f"An unexpected error occurred while fetching detailed info for '{filename}': {e}"
        )
        return None


def extract_artist_and_title(filename):
    """Extract the artist and title from the filename using regex and clean up."""
    # Try to extract artist and title using a common format like "Artist - Title.mp3"
    match = re.match(r"^(.*?)\s*[-–]\s*(.*?)(\.mp3)$", filename, re.IGNORECASE)
    if match:
        artist = match.group(1).strip()
        title = match.group(2).strip()

        # Remove featuring artists and other extraneous details from the title
        title = re.sub(r"\(feat[^\)]*\)", "", title).strip()  # Remove "(feat. Artist)"
        title = re.sub(
            r"\(.*\)", "", title
        ).strip()  # Remove anything inside parentheses
        title = re.sub(
            r"\s+", " ", title
        )  # Replace multiple spaces with a single space

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
