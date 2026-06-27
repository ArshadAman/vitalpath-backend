import logging
from app.celery_app import celery
from app.core.database import SessionLocal
from app.features.voice.services import process_voice_journal

logger = logging.getLogger(__name__)

@celery.task(name="voice.process_audio")
def process_audio_journal_task(user_id: int, file_path: str, language: str):
    """Celery background task simulating speech-to-text transcription and health event logging."""
    logger.info(f"Celery transcribing audio file for user: {user_id} with language: {language}")
    db = SessionLocal()
    try:
        # Default mock transcript
        mock_transcript = "I smoked 2 cigarettes today."
        
        # Expand mock responses based on specified language for demonstration
        if language == "hi": # Hindi
            mock_transcript = "मैंने आज 2 सिगरेट पी।"
        elif language == "ta": # Tamil
            mock_transcript = "நான் இன்று 2 சிகரெட் பிடித்தேன்."
        elif language == "te": # Telugu
            mock_transcript = "నేను ఈ రోజు 2 సిగరెట్లు తాగాను."
            
        process_voice_journal(db, user_id, mock_transcript, language, file_path)
        logger.info(f"Voice journal logging complete for user ID: {user_id}")
        return True
    except Exception as e:
        logger.exception(f"Error in speech-to-text processing: {e}")
        return False
    finally:
        db.close()
