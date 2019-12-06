import argparse as ap
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util
import pickle
from datetime import date

if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Check for a playlist-URL or URI, which entries are new since the last check'
                                           'those are added to a newly created playlist in your account')
    parser.add_argument('--URI', default=None, help='Playlist URI')
    parser.add_argument('--URL', default=None, help='Playlist URL for an public playlist')
    parser.add_argument('--create', default=True, help='Create a playlist from the new tracks')
    args = parser.parse_args()

    client_credentials_manager = SpotifyClientCredentials(client_id='f6a685b72991467fbb9b45ca9a39ffaf', client_secret='c0d27814ffc84b289ca0611f3dae6c25')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    uri = args.URI
    url = args.URL
    if uri is not None:
        username = 'spotify'
        playlist_id = uri.split(':')[-1]
        with open("latest.pickle", "wb") as pickle_out:
            pickle.dump([username, playlist_id], pickle_out)
    elif url is not None:
        username = 'spotify'
        playlist_id = url.split('/')[-1].split('?')[0]
        with open("latest.pickle", "wb") as pickle_out:
            pickle.dump([username, playlist_id], pickle_out)
    else:
        pickle_in = open("latest.pickle", "rb")
        [username, playlist_id] = pickle.load(pickle_in)

    # load old songs
    old_songs = pd.read_csv('database.csv', index_col=0)

    # Get all tracks
    results = sp.user_playlist_tracks(username, playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Create df for new songs
    artists = []
    names = []
    uris = []
    for i, track in enumerate(tracks):
        try:
            art = [track['track']['artists'][0]['name']]
            nam = [track['track']['name']]
            ur = [track['track']['uri']]
        except TypeError:
            print('Fehlerhafter Track %d' % i)
            continue
        artists += art
        names += nam
        uris += ur
    new_songs = pd.DataFrame({'artist': artists, 'name': names, 'uri': uris, 'playlist_id': len(names) * [playlist_id]})

    # Get new tracks
    useful_old_songs = old_songs.loc[old_songs['playlist_id'] == playlist_id]
    to_add = new_songs.loc[new_songs['uri'].isin(useful_old_songs['uri'].values) == False]
    old_songs = old_songs.append(to_add)

    # Save current state
    old_songs.to_csv('database.csv')
    if args.create == True:
        if len(to_add) > 0:
            # Auth
            scope = 'playlist-modify-public'
            username = input('Username:')
            token = util.prompt_for_user_token(username, scope, client_id='f6a685b72991467fbb9b45ca9a39ffaf',
                                               client_secret='c0d27814ffc84b289ca0611f3dae6c25', redirect_uri='http://127.0.0.1')

            if token:
                sp = spotipy.Spotify(auth=token)
                sp.trace = False
                # Create a playlist with new songs
                pl = sp.user_playlist(username, playlist_id)
                pl_name = pl['name'] + date.today().strftime(" %b-%d-%Y")
                created_playlist = sp.user_playlist_create(username, pl_name)
                sp.user_playlist_add_tracks(username, created_playlist['uri'], to_add['uri'].values)
                print('Playlist \'%s\' created' % pl_name)
            else:
                print("Can't get token for", username)
        else:
            print('Everything up to date')