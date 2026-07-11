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
    status: str = "processing"
    event_data: Optional[dict] = None
    is_committed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
