import argparse as ap
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import spotipy.util as util
import pickle
from datetime import date


def main():
    parser = ap.ArgumentParser(description='Check for a playlist-URL or URI, which entries are new since the last check'
                                           'those are added to a newly created playlist in your account')
    parser.add_argument('--URI', default=None, help='Playlist URI')
    parser.add_argument('--URL', default=None, help='Playlist URL for an public playlist')
    parser.add_argument('--col', default=None, help='Playlist Collection for an public playlist')
    parser.add_argument('--create', default=True, help='Create a playlist from the new tracks')
    parser.add_argument('--user', default=None, help='Use the account specified by this username')
    parser.add_argument('--add', default=None, help='add the uri/url to a collection with this name')
    args = parser.parse_args()

    client_credentials_manager = SpotifyClientCredentials(client_id='f6a685b72991467fbb9b45ca9a39ffaf', client_secret='c0d27814ffc84b289ca0611f3dae6c25')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    # Load latest
    try:
        pickle_in = open("latest.pickle", "rb")
    except FileNotFoundError:
        with open("latest.pickle", "wb") as pickle_out:
            pickle.dump([None, None, None, dict()], pickle_out)
    pickle_in = open("latest.pickle", "rb")
    [pl_username, playlist_id, username, cols] = pickle.load(pickle_in)

    if args.col is not None:
        if args.col not in cols.keys():
            print("No Collection with this name")
            return
        pl_list = cols[args.col]
    elif args.URI is not None:
        pl_username = 'spotify'
        playlist_id = args.URI.split(':')[-1]
        pl_list = [(pl_username, playlist_id)]
    elif args.URL is not None:
        pl_username = 'spotify'
        playlist_id = args.URL.split('/')[-1].split('?')[0]
        pl_list = [(pl_username, playlist_id)]
    if args.user is not None:
        username = args.user
    if username is None:
        username = input('Username:')
    if playlist_id is None or pl_username is None:
        print('No Playlist specified')
        return

    # add to collection
    collection_name = args.add
    if collection_name is not None:
        if collection_name not in cols.keys():
            cols[collection_name] = []
        cols[collection_name] += [(pl_username, playlist_id)]
    #Save latest
    with open("latest.pickle", "wb") as pickle_out:
        pickle.dump([pl_username, playlist_id, username, cols], pickle_out)

    # load old songs
    old_songs = pd.read_csv('database.csv', index_col=0)

    for pl_username, playlist_id in pl_list:
        # Get all tracks
        results = sp.user_playlist_tracks(pl_username, playlist_id)
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
        # Use all
        # useful_old_songs = old_songs.loc[old_songs['playlist_id'] == playlist_id]
        useful_old_songs = old_songs
        to_add = new_songs.loc[new_songs['uri'].isin(useful_old_songs['uri'].values) == False]
        old_songs = old_songs.append(to_add)

        # Save current state
        old_songs.to_csv('database.csv')
        if args.create == True:
            if len(to_add) > 0:
                # Auth
                scope = 'playlist-modify-public'
                token = util.prompt_for_user_token(username, scope, client_id='f6a685b72991467fbb9b45ca9a39ffaf',
                                                   client_secret='c0d27814ffc84b289ca0611f3dae6c25', redirect_uri='http://127.0.0.1')

                if token:
                    sp = spotipy.Spotify(auth=token)
                    sp.trace = False
                    # Create a playlist with new songs
                    pl = sp.user_playlist(username, playlist_id)
                    pl_name = pl['name'] + date.today().strftime(" %b-%d-%Y")
                    created_playlist = sp.user_playlist_create(username, pl_name)
                    to_add_songs = to_add['uri'].values
                    while len(to_add_songs) > 0:
                        sp.user_playlist_add_tracks(username, created_playlist['uri'], to_add_songs[:90])
                        to_add_songs = to_add_songs[90:]
                    print('Playlist \'%s\' created' % pl_name)
                else:
                    print("Can't get token for", username)
            else:
                print('Everything up to date - %s' % playlist_id)


if __name__ == '__main__':
    main()