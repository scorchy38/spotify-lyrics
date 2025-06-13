from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from syrics.api import Spotify
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lyrics API", description="Lyrics fetching service for YouTube videos")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Spotify clients
try:
    # Official Spotify API for track searching
    spotify_api = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        )
    )

    # Syrics for lyrics fetching
    lyrics_api = Spotify(os.getenv("SPOTIFY_SP_DC"))

except Exception as e:
    logger.error(f"Failed to initialize Spotify clients: {e}")
    spotify_api = None
    lyrics_api = None


# Pydantic models
class Track(BaseModel):
    id: str
    name: str
    artists: List[Dict[str, Any]]
    albumOfTrack: Dict[str, Any]
    durationMs: int


class LyricsLine(BaseModel):
    startTimeMs: str
    words: str
    syllables: List[Any]
    endTimeMs: str


class LyricsData(BaseModel):
    syncType: str
    lines: List[LyricsLine]
    provider: str
    providerLyricsId: str
    providerDisplayName: str
    syncLyricsUri: str
    isDenseTypeface: bool
    alternatives: List[Any]
    language: str
    isRtlLanguage: bool
    capStatus: str


class LyricsResponse(BaseModel):
    lyrics: LyricsData
    offset: int


class ErrorResponse(BaseModel):
    error: str


class GetTracksRequest(BaseModel):
    query: str


class FetchLyricsWithTrackRequest(BaseModel):
    videoID: str
    track: Track


class FetchLyricsWithQueryRequest(BaseModel):
    videoID: str
    query: str


class SetOffsetRequest(BaseModel):
    videoID: str
    offset: int


def transform_spotify_track_to_extension_format(track_data: Dict) -> Track:
    """Transform Spotify API track data to extension format"""
    try:
        # Extract album cover art
        album_images = track_data['album'].get('images', [])
        cover_art_sources = [{"url": img["url"]} for img in album_images]

        return Track(
            id=track_data['id'],
            name=track_data['name'],
            artists=[{"name": artist["name"]} for artist in track_data['artists']],
            albumOfTrack={
                "name": track_data['album']['name'],
                "coverArt": {
                    "sources": cover_art_sources
                }
            },
            durationMs=track_data['duration_ms']
        )
    except KeyError as e:
        logger.error(f"Error transforming track data: {e}")
        raise HTTPException(status_code=500, detail="Error processing track data")


def transform_syrics_lyrics_to_extension_format(syrics_data: Dict) -> LyricsData:
    """Transform syrics lyrics data to extension format"""
    try:
        lines = []

        # Handle different syrics response formats
        if 'lyrics' in syrics_data and 'lines' in syrics_data['lyrics']:
            syrics_lines = syrics_data['lyrics']['lines']
        elif 'lines' in syrics_data:
            syrics_lines = syrics_data['lines']
        else:
            # If no synchronized lyrics, create a simple format
            return LyricsData(
                syncType="UNSYNCED",
                lines=[],
                provider="Syrics",
                providerLyricsId="",
                providerDisplayName="Syrics",
                syncLyricsUri="",
                isDenseTypeface=False,
                alternatives=[],
                language="en",
                isRtlLanguage=False,
                capStatus="NONE"
            )

        # Transform lines
        for line in syrics_lines:
            lines.append(LyricsLine(
                startTimeMs=str(line.get('startTimeMs', '0')),
                words=line.get('words', ''),
                syllables=[],
                endTimeMs=str(line.get('endTimeMs', '0'))
            ))

        return LyricsData(
            syncType="LINE_SYNCED" if lines and any(line.startTimeMs != '0' for line in lines) else "UNSYNCED",
            lines=lines,
            provider="Syrics",
            providerLyricsId=str(syrics_data.get('id', '')),
            providerDisplayName="Syrics",
            syncLyricsUri="",
            isDenseTypeface=False,
            alternatives=[],
            language=syrics_data.get('language', 'en'),
            isRtlLanguage=False,
            capStatus="NONE"
        )
    except Exception as e:
        logger.error(f"Error transforming lyrics data: {e}")
        raise HTTPException(status_code=500, detail="Error processing lyrics data")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "lyrics-api"}


@app.post("/getTracks")
async def get_tracks(request: GetTracksRequest) -> List[Track]:
    """Search for tracks using Spotify API"""
    if not spotify_api:
        raise HTTPException(status_code=503, detail="Spotify API not available")

    try:
        # Search for tracks
        results = spotify_api.search(q=request.query, type='track', limit=30)
        tracks = []

        for item in results['tracks']['items']:
            track = transform_spotify_track_to_extension_format(item)
            tracks.append(track)
        print(tracks)
        return tracks

    except Exception as e:
        logger.error(f"Error searching tracks: {e}")
        raise HTTPException(status_code=500, detail="Error searching for tracks")


@app.post("/fetchLyrics")
async def fetch_lyrics(
        request: Union[FetchLyricsWithTrackRequest, FetchLyricsWithQueryRequest]
) -> Union[LyricsResponse, ErrorResponse]:
    """Fetch lyrics for a track or search query"""
    if not lyrics_api:
        raise HTTPException(status_code=503, detail="Lyrics API not available")

    try:
        track_id = None

        # If we have a track object, use its ID
        if hasattr(request, 'track') and request.track:
            track_id = request.track.id
        else:
            # Search for the track first
            if not spotify_api:
                return ErrorResponse(error="LoggedOut")

            results = spotify_api.search(q=request.query, type='track', limit=1)
            if not results['tracks']['items']:
                return ErrorResponse(error="TrackNotFound")

            track_id = results['tracks']['items'][0]['id']

        # Fetch lyrics using syrics
        try:
            syrics_response = lyrics_api.get_lyrics(track_id)

            if not syrics_response:
                return ErrorResponse(error="LyricsNotFound")

            # Transform to extension format
            lyrics_data = transform_syrics_lyrics_to_extension_format(syrics_response)

            print(lyrics_data)

            return LyricsResponse(
                lyrics=lyrics_data,
                offset=0
            )

        except Exception as lyrics_error:
            logger.error(f"Error fetching lyrics for track {track_id}: {lyrics_error}")
            return ErrorResponse(error="LyricsNotFound")

    except Exception as e:
        logger.error(f"Error in fetch_lyrics: {e}")
        return ErrorResponse(error="UnknownError")


@app.post("/setOffset")
async def set_offset(request: SetOffsetRequest):
    """Set offset for a video (placeholder - implement with your storage solution)"""
    try:
        # This would typically save to a database
        # For now, just return success
        logger.info(f"Setting offset {request.offset} for video {request.videoID}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error setting offset: {e}")
        raise HTTPException(status_code=500, detail="Error setting offset")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3839)