from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VoiceJournalResponse(BaseModel):
    id: int
    user_id: int
    audio_file_path: Optional[str] = None
    transcription: str
    language: str
    detected_intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
