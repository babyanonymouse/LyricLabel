import requests

# Replace with your own Last.fm API key
LASTFM_API_KEY = '0526879300a394a39f059a5c1975fc01'

def fetch_metadata_from_lastfm(song_name, artist_name=None):
    # Search for the song first using the track.search method
    search_url = f'http://ws.audioscrobbler.com/2.0/?method=track.search&track={song_name}&api_key={LASTFM_API_KEY}&format=json'
    
    try:
        # Make a request to the search API
        search_response = requests.get(search_url)
        search_data = search_response.json()

        # Check if any tracks were found
        if 'results' in search_data and 'trackmatches' in search_data['results']:
            tracks = search_data['results']['trackmatches']['track']
            if tracks:
                track = tracks[0]  # Taking the first match

                # Use track.getInfo to fetch detailed info about the track
                track_info_url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={track["artist"]}&track={track["name"]}&api_key={LASTFM_API_KEY}&format=json'
                track_info_response = requests.get(track_info_url)
                track_info_data = track_info_response.json()

                if 'track' in track_info_data:
                    track_details = track_info_data['track']
                    metadata = {
                        'artist': track_details['artist']['name'],
                        'album': track_details.get('album', {}).get('title', 'Unknown'),
                        'track': track_details['name'],
                        'genre': track_details.get('toptags', {}).get('tag', [{}])[0].get('name', 'Unknown'),
                        'year': track_details.get('release_date', 'Unknown')[:4]  # Extracting the year correctly
                    }
                    return metadata
                else:
                    print("Detailed info could not be fetched.")
                    return None
            else:
                print("No matching tracks found for:", song_name)
                return None
        else:
            print("No results found for song:", song_name)
            return None
    except Exception as e:
        print("Error fetching metadata:", e)
        return None

def main():
    # Ask user for song name (or filename)
    song_name = input("Enter the name or filename of the song: ")

    # Fetch metadata from Last.fm
    metadata = fetch_metadata_from_lastfm(song_name)
    
    if metadata:
        print("\nSong Metadata:")
        print(f"Artist: {metadata['artist']}")
        print(f"Album: {metadata['album']}")
        print(f"Track: {metadata['track']}")
        print(f"Genre: {metadata['genre']}")
        print(f"Year: {metadata['year']}")
    else:
        print("Metadata could not be fetched.")

if __name__ == "__main__":
    main()
