import time
import spotipy
from ytmusicapi import YTMusic

from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

import os
from dotenv import load_dotenv

load_dotenv()

# Spotify API
clientId = os.getenv("CLIENT_ID")
clientSecret = os.getenv("CLIENT_SECRET")

print(clientId, clientSecret)

# Youtube Music API

ytmusic = YTMusic("oauth.json")

'''
playlistId = ytmusic.create_playlist("test", "test description")
search_results = ytmusic.search("Oasis Wonderwall", "songs")
ytmusic.add_playlist_items(playlistId, [search_results[1]['videoId']])
'''
# TODO get play lists names from spotify and create all the playlists
# TODO Get all the names from the playlist, search for it, get the artist name to help
# TODO if no match then skip it
# TODO clean up code
# Search by "song name, artist name" , filter "songs"







# initialize Flask app
app = Flask(__name__)

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = 'sfhakjhfw21423421'

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'


# route to handle logging in
@app.route('/')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)


# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the save_discover_weekly route
    return redirect(url_for('spotifyToYTMusic', _external=True))


# route to save the Discover Weekly songs to a playlist
@app.route('/spotifyToYTMusic')
def spotifyToYTMusic():
    spotifyPlaylists = getPlaylists()
    for playlist in spotifyPlaylists:
        playlist_name = playlist['name']
        # create playlist in YTMusic
        playlistId = ytmusic.create_playlist(playlist_name, "Spotify Playlist from Converter")
        for song in playlist['songs']:
            song_name = song['name'].lower()
            song_artists = song['artists']
            string_artists = ''
            for x in song_artists:
                string_artists += x + " "
            query = song_name + " by " + string_artists
            # search songs, filter for songs only
            search_results = ytmusic.search(query, "songs")
            # find the song that matches closest
            closest_result = ''
            similar_artist_count = -1
            for result in search_results:
                video_id = result['videoId']
                result_name = result['title'].lower()
                result_artists = [x['name'] for x in result['artists']]
                if song_name == result_name:
                    similar_artists = len(set(song_artists) & set(result_artists))
                    if similar_artists > similar_artist_count:
                        # test closest_result = result_name + ''.join(result_artists)
                        closest_result = video_id
                        similar_artist_count = similar_artists
            # test print(closest_result)
            ytmusic.add_playlist_items(playlistId, closest_result)
        break
    return spotifyPlaylists


def getPlaylists():
    try:
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # get the user's playlists
    current_playlists = sp.current_user_playlists()['items']
    # name
    playlists = []
    for playlist in current_playlists:
        playlistId = playlist["id"]
        data = {'name': playlist['name'], 'songs': getSongs(playlistId)}
        playlists.append(data)
    return playlists


def getSongs(playlist):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    data = sp.playlist(playlist)
    songs = []
    for song in data["tracks"]["items"]:
        song = song["track"]
        artists = song["artists"]
        artists = [artist['name'] for artist in artists]
        data = {'name': song['name'], 'artists': artists}
        songs.append(data)
    return songs


# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))

    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=clientId,
        client_secret=clientSecret,
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private'
    )


app.run(debug=True)
