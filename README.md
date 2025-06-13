# Spotify Lyrics API

A simple FastAPI service that fetches synchronized lyrics from Spotify for hobby music apps that need real-time lyrics display using Spotify python client and [syrics](https://github.com/akashrchandran/syrics/)!

## Quick Start

1. Clone the repo
```bash
git clone https://github.com/scorchy38/spotify-lyrics.git
cd spotify-lyrics
```

2. Install dependencies
```bash
uv pip install -e .
```

3. Set up your environment variables
```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret  
SPOTIFY_SP_DC=your_sp_dc_cookie
REDIS_URL=your_redis_url
```

4. Run it
```bash
uv run main.py
```

## API Endpoints

- `POST /getTracks` - Search for tracks
- `POST /fetchLyrics` - Get lyrics for a track or query
- `POST /setOffset` - Set timing offset for a video

## Note

You'll need a Spotify Developer account and the `sp_dc` cookie from your Spotify session for lyrics access.