from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class VoiceJournalLog(Base):
    __tablename__ = "voice_journal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    audio_file_path = Column(String, nullable=True)
    transcription = Column(String)
    language = Column(String)
    detected_intent = Column(String, nullable=True) # e.g., Smoking Event
    created_at = Column(DateTime, default=datetime.utcnow)
