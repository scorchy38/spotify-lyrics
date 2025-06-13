from typing import Dict

from fastapi import HTTPException

from src.models.lyrics import LyricsData, LyricsLine
from src.models.requests import Track


class Utils:
    @staticmethod
    def transform_spotify_track_to_extension_format(track_data: Dict) -> Track:
        try:
            album_images = track_data['album'].get('images', [])
            cover_art_sources = [{"url": img["url"]} for img in album_images]

            return Track(
                id=track_data['id'],
                name=track_data['name'],
                artists={
                    "items": [{"profile": {"name": artist["name"]}} for artist in track_data['artists']]
                },
                albumOfTrack={
                    "name": track_data['album']['name'],
                    "coverArt": {
                        "sources": cover_art_sources
                    }
                },
                durationMs=track_data['duration_ms']
            )
        except KeyError as e:
            raise HTTPException(status_code=500, detail=f"Error processing track data {e}")

    @staticmethod
    def transform_syrics_lyrics_to_extension_format(syrics_data: Dict) -> LyricsData:
        try:
            lines = []

            if 'lyrics' in syrics_data and 'lines' in syrics_data['lyrics']:
                syrics_lines = syrics_data['lyrics']['lines']
            elif 'lines' in syrics_data:
                syrics_lines = syrics_data['lines']
            else:
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
            raise HTTPException(status_code=500, detail=f"Error processing lyrics data: {e}")
