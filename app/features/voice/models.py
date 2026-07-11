from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
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
    status = Column(String, default="processing")   # processing, completed, failed
    is_committed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
