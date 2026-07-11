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
    intent: Optional[str] = None,
    status: str = "processing",
    is_committed: bool = False
) -> VoiceJournalLog:
    """Saves voice journal log details to database."""
    log = VoiceJournalLog(
        user_id=user_id,
        audio_file_path=audio_path,
        transcription=transcription,
        language=language,
        detected_intent=intent,
        status=status,
        is_committed=is_committed
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def parse_voice_intent(text: str) -> Dict[str, Any]:
    """Extracts structured clinical/lifestyle events from English or Hinglish text."""
    text_lower = text.lower()
    
    # Try to extract first number found in the text for dosage/quantities
    count = 1
    for word in text_lower.split():
        # clean punctuation
        cleaned = "".join(c for c in word if c.isdigit())
        if cleaned:
            count = int(cleaned)
            break

    # 1. Smoking / Nicotine
    if any(kw in text_lower for kw in ["smoke", "cigarette", "sutta", "sigret", "सिगरेट", "tobacco"]):
        return {
            "event_type": "lifestyle_event",
            "title": "Smoking Event",
            "description": f"Logged via Voice: smoked {count} cigarette(s).",
            "payload": {"substance": "nicotine", "cigarettes_count": count}
        }
        
    # 2. Exercise / Activity
    elif any(kw in text_lower for kw in ["walk", "run", "exercise", "daudha", "daudhi", "bhaga", "gym", "kasrat", "कसरत", "workout", "steps"]):
        val_str = f"{count} km" if "km" in text_lower or "kilometer" in text_lower or "daudh" in text_lower else f"{count} units"
        if "step" in text_lower:
            val_str = f"{count} steps"
        return {
            "event_type": "exercise",
            "title": "Logged Workout via Voice",
            "description": text,
            "payload": {"workout_type": "cardio", "logged_via": "voice", "value": val_str}
        }
        
    # 3. Alcohol / Intake
    elif any(kw in text_lower for kw in ["daaru", "beer", "wine", "drink kiya", "drink ki", "sharab", "शराब", "alcohol"]):
        return {
            "event_type": "lifestyle_event",
            "title": "Alcohol Intake",
            "description": f"Logged via Voice: {count} glass/can of alcohol.",
            "payload": {"substance": "alcohol", "quantity": f"{count} glasses"}
        }

    # 4. Sleep
    elif any(kw in text_lower for kw in ["soya", "soyi", "neend", "sleep", "so gaya", "so gayi", "नींद", "ghante"]):
        return {
            "event_type": "sleep",
            "title": "Logged Sleep via Voice",
            "description": f"Logged via Voice: {count} hours of sleep.",
            "payload": {"hours": count, "logged_via": "voice"}
        }

    # 5. Hydration / Water
    elif any(kw in text_lower for kw in ["paani", "water", "glass water", "glass paani", "पानी"]):
        return {
            "event_type": "hydration",
            "title": "Logged Hydration via Voice",
            "description": f"Logged via Voice: drank {count} glasses of water.",
            "payload": {"glasses": count, "logged_via": "voice"}
        }

    # 6. Medication
    elif any(kw in text_lower for kw in ["dawai", "medicine", "goli", "tablet", "दवाई"]):
        return {
            "event_type": "lifestyle_event",
            "title": "Medication Logged",
            "description": f"Logged via Voice: took medication.",
            "payload": {"medication_taken": True, "logged_via": "voice"}
        }
        
    return {
        "event_type": "voice_note",
        "title": "General Voice Entry",
        "description": text,
        "payload": {}
    }

def process_voice_journal(db: Session, user_id: int, transcript: str, language: str, audio_path: Optional[str] = None) -> VoiceJournalLog:
    """Processes transcription, extracts structured events, inserts into the timeline, and marks status as completed."""
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
    
    # Save transcription log as completed and committed
    return create_voice_log(db, user_id, transcript, language, audio_path, parsed["title"], status="completed", is_committed=True)
