import os

import spotipy
from spotipy import SpotifyClientCredentials
from syrics.api import Spotify


class ClientsService:
    def __init__(self):
        self._spotify_client = None
        self._syrics_client = None

    def get_spotify_client(self):
        if self._spotify_client is None:
            self._spotify_client = spotipy.Spotify(
                client_credentials_manager=SpotifyClientCredentials(
                    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
                )
            )
        return self._spotify_client

    def get_syrics_client(self):
        if self._syrics_client is None:
            self._syrics_client = Spotify(os.getenv("SPOTIFY_SP_DC"))
        return self._syrics_client
