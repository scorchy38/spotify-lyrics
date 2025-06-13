from typing import List, Any

from pydantic import BaseModel


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