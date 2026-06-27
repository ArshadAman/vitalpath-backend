from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
from app.features.voice.models import VoiceJournalLog
from app.features.timeline.services import create_timeline_event
from app.features.timeline.schemas import TimelineEventCreate

def create_voice_log(
    db: Session, 
    user_id: int, 
    transcription: str, 
    language: str, 
    audio_path: Optional[str] = None,
    intent: Optional[str] = None
) -> VoiceJournalLog:
    """Saves voice journal log details to database."""
    log = VoiceJournalLog(
        user_id=user_id,
        audio_file_path=audio_path,
        transcription=transcription,
        language=language,
        detected_intent=intent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def parse_voice_intent(text: str) -> Dict[str, Any]:
    """Mock NLP intent parser converting voice text to structured parameters."""
    text_lower = text.lower()
    
    if "smoke" in text_lower or "cigarette" in text_lower:
        # Example: "I smoked 2 cigarettes today"
        count = 1
        for word in text_lower.split():
            if word.isdigit():
                count = int(word)
                break
        return {
            "event_type": "lifestyle_event",
            "title": "Smoking Event",
            "description": f"User reported smoking {count} cigarette(s).",
            "payload": {"substance": "nicotine", "cigarettes_count": count}
        }
        
    elif "walk" in text_lower or "run" in text_lower or "exercise" in text_lower:
        return {
            "event_type": "exercise",
            "title": "Logged Workout via Voice",
            "description": text,
            "payload": {"workout_type": "cardio", "logged_via": "voice"}
        }
        
    return {
        "event_type": "voice_note",
        "title": "General Voice Entry",
        "description": text,
        "payload": {}
    }

def process_voice_journal(db: Session, user_id: int, transcript: str, language: str, audio_path: Optional[str] = None) -> VoiceJournalLog:
    """Processes transcription, extracts structured events, and inserts into the timeline."""
    parsed = parse_voice_intent(transcript)
    
    # Create the structured timeline event
    event_data = TimelineEventCreate(
        event_type=parsed["event_type"],
        event_date=datetime.utcnow(),
        title=parsed["title"],
        description=parsed["description"],
        payload=parsed["payload"]
    )
    create_timeline_event(db, user_id, event_data)
    
    # Save transcription log
    return create_voice_log(db, user_id, transcript, language, audio_path, parsed["title"])
