import logging
from typing import List, Union

from fastapi import APIRouter, HTTPException

from src.clients.factory import ClientsFactory
from src.models.errors import ErrorResponse
from src.models.requests import GetTracksRequest, Track, FetchLyricsWithTrackRequest, FetchLyricsWithQueryRequest, \
    SetOffsetRequest
from src.offset_service import OffsetService
from src.utils import Utils

router = APIRouter()
logger = logging.getLogger(__name__)
offset_service = OffsetService()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "lyrics-api"}


@router.post("/getTracks")
async def get_tracks(request: GetTracksRequest) -> List[Track]:
    clients = ClientsFactory.get_instance()
    spotify = clients.get_spotify_client()
    try:
        results = spotify.search(q=request.query, type='track', limit=30)
        tracks = []

        for item in results['tracks']['items']:
            track = Utils.transform_spotify_track_to_extension_format(item)
            tracks.append(track)
        return tracks

    except Exception as e:
        logger.error(f"Error searching tracks: {e}")
        raise HTTPException(status_code=500, detail="Error searching for tracks")


@router.post("/fetchLyrics")
async def fetch_lyrics(
        request: Union[FetchLyricsWithTrackRequest, FetchLyricsWithQueryRequest]
) -> Union[dict, ErrorResponse]:
    clients = ClientsFactory.get_instance()
    spotify = clients.get_spotify_client()
    syrics = clients.get_syrics_client()
    try:
        if hasattr(request, 'track') and request.track:
            track_id = request.track.id
        else:
            results = spotify.search(q=request.query, type='track', limit=1)
            if not results['tracks']['items']:
                return ErrorResponse(error="TrackNotFound")

            track_id = results['tracks']['items'][0]['id']

        try:
            syrics_response = syrics.get_lyrics(track_id)

            if not syrics_response:
                return ErrorResponse(error="LyricsNotFound")

            lyrics_data = Utils.transform_syrics_lyrics_to_extension_format(syrics_response)

            video_offset = await offset_service.get_video_offset(request.videoID) if hasattr(request, 'videoID') else 0

            response_data = {
                "lyrics": {
                    "syncType": lyrics_data.syncType,
                    "lines": [line.model_dump() for line in lyrics_data.lines],
                    "provider": lyrics_data.provider,
                    "providerLyricsId": lyrics_data.providerLyricsId,
                    "providerDisplayName": lyrics_data.providerDisplayName,
                    "syncLyricsUri": lyrics_data.syncLyricsUri,
                    "isDenseTypeface": lyrics_data.isDenseTypeface,
                    "alternatives": lyrics_data.alternatives,
                    "language": lyrics_data.language,
                    "isRtlLanguage": lyrics_data.isRtlLanguage,
                    "capStatus": lyrics_data.capStatus,
                    "colors": {
                        "background": 3429719594,
                        "text": 3019898879,
                        "highlightText": 4278255615
                    }
                },
                "offset": video_offset
            }
            return response_data

        except Exception as lyrics_error:
            logger.error(f"Error fetching lyrics for track {track_id}: {lyrics_error}")
            return ErrorResponse(error="LyricsNotFound")

    except Exception as e:
        logger.error(f"Error in fetch_lyrics: {e}")
        return ErrorResponse(error="UnknownError")


@router.post("/setOffset")
async def set_offset(request: SetOffsetRequest):
    try:
        await offset_service.set_video_offset(request.videoID, request.offset)
        logger.info(f"Setting offset {request.offset} for video {request.videoID}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Error setting offset: {e}")
        raise HTTPException(status_code=500, detail="Error setting offset")
