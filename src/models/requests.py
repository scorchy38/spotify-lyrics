from typing import Dict, Any

from pydantic import BaseModel


class Track(BaseModel):
    id: str
    name: str
    artists: dict[str, list[dict[str, dict[str, Any]]]]
    albumOfTrack: Dict[str, Any]
    durationMs: int

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
