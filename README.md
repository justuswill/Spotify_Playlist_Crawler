# Spotify_Playlist_Crawler
A Crawler that keeps track of an public playlist and can be invoked to look what songs changed since the last time.
It than creates an new playlist with all new songs in your account.
The first time you use it you have to sign in to your account by following a link and copying a URL. Details are in the terminal.
If no URL/URI is giving it uses the last recently used one

Requires:
Python 3
Pandas
Spotipy

Usage:

'check_playlist.py --help
>
> Check for a playlist-URL or URI, which entries are new since the last check
> those are added to a newly created playlist in your account
>
> optional arguments:
>   -h, --help       show this help message and exit
>   --URI URI        Playlist URI
>   --URL URL        Playlist URL for an public playlist
>   --create CREATE  Create a playlist from the new tracks'

'python check_playlist.py --URL 'https://open.spotify.com/playlist/37i9dQZF1DX8AliSIsGeKd?si=n5K8tOzXSwGg8yMcDBihUQ'
> Username:<enter_your_username>
> Playlist 'Electronic Rising Dec-06-2019' created'

'python check_playlist.py
> Everything up to date'


