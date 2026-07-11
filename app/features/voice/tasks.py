import logging
from app.celery_app import celery
from app.core.database import SessionLocal
from app.features.voice.models import VoiceJournalLog
from app.features.voice.services import process_voice_journal, parse_voice_intent
from app.features.voice.transcribe import transcribe_audio_whisper
from app.features.timeline.services import create_timeline_event
from app.features.timeline.schemas import TimelineEventCreate
from datetime import datetime

logger = logging.getLogger(__name__)

@celery.task(name="voice.process_audio")
def process_audio_journal_task(voice_log_id: int, file_path: str, language: str):
    """Celery background task running real speech-to-text transcription via Whisper and event parsing."""
    logger.info(f"Celery processing audio for voice log: {voice_log_id} with language: {language}")
    db = SessionLocal()
    try:
        # Fetch the voice log
        voice_log = db.query(VoiceJournalLog).filter(VoiceJournalLog.id == voice_log_id).first()
        if not voice_log:
            logger.error(f"Voice journal log ID {voice_log_id} not found in database.")
            return False

        # Run transcription using self-hosted Whisper
        try:
            transcript = transcribe_audio_whisper(file_path, language)
            if not transcript:
                raise ValueError("Whisper returned empty transcription")
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            voice_log.status = "failed"
            db.commit()
            return False

        # Process intent
        parsed = parse_voice_intent(transcript)
        
        # Update log
        voice_log.transcription = transcript
        voice_log.detected_intent = parsed["title"]
        voice_log.status = "completed"
        db.commit()
        
        logger.info(f"Voice journal log {voice_log_id} completed successfully.")
        return True
        
    except Exception as e:
        logger.exception(f"Error in speech-to-text task processing: {e}")
        try:
            voice_log = db.query(VoiceJournalLog).filter(VoiceJournalLog.id == voice_log_id).first()
            if voice_log:
                voice_log.status = "failed"
                db.commit()
        except Exception:
            pass
        return False
    finally:
        db.close()
