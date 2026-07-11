from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from app.core.database import get_db
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.voice.schemas import VoiceJournalResponse
from app.features.voice.tasks import process_audio_journal_task
from app.features.voice.services import create_voice_log, parse_voice_intent
from app.features.voice.models import VoiceJournalLog
from app.features.timeline.schemas import TimelineEventCreate
from app.features.timeline.services import create_timeline_event
from app.features.score.services import calculate_health_metrics
from typing import List

router = APIRouter(prefix="/voice", tags=["Voice Health Journal"])

UPLOAD_DIR = "/workspace/uploads/voice"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/journal", response_model=VoiceJournalResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_voice_journal(
    language: str = Form("hi"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uploads user voice recording to be transcribed and structured into events asynchronously."""
    # Ensure correct filename format
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB entry with 'processing' status
    voice_log = create_voice_log(
        db=db,
        user_id=current_user.id,
        transcription="Processing speech in background...",
        language=language,
        audio_path=file_path,
        intent="Pending",
        status="processing"
    )
    
    # Offload processing to background Celery worker using the real log ID
    process_audio_journal_task.delay(voice_log.id, file_path, language)
    
    return voice_log

@router.get("/journal/{journal_id}/status", response_model=VoiceJournalResponse)
def get_voice_journal_status(
    journal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Checks the transcription & intent parsing status of a voice log."""
    voice_log = db.query(VoiceJournalLog).filter(
        VoiceJournalLog.id == journal_id,
        VoiceJournalLog.user_id == current_user.id
    ).first()
    
    if not voice_log:
        raise HTTPException(status_code=404, detail="Voice journal entry not found")
        
    return voice_log

@router.get("/journals", response_model=List[VoiceJournalResponse])
def get_voice_journals_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the last 10 committed voice journals transcribed by the current user."""
    logs = db.query(VoiceJournalLog).filter(
        VoiceJournalLog.user_id == current_user.id,
        VoiceJournalLog.is_committed == True
    ).order_by(VoiceJournalLog.created_at.desc()).limit(10).all()
    
    return logs

@router.post("/journal/{journal_id}/commit", response_model=VoiceJournalResponse)
def commit_voice_journal(
    journal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Commits a transcribed voice journal entry to the timeline."""
    voice_log = db.query(VoiceJournalLog).filter(
        VoiceJournalLog.id == journal_id,
        VoiceJournalLog.user_id == current_user.id
    ).first()
    
    if not voice_log:
        raise HTTPException(status_code=404, detail="Voice journal entry not found")
        
    if voice_log.status != "completed":
        raise HTTPException(status_code=400, detail="Voice journal transcription is not complete")
        
    if voice_log.is_committed:
        # Already committed, return log directly
        return voice_log
        
    # Process intent from the completed transcription
    parsed = parse_voice_intent(voice_log.transcription)
    
    # Create the structured timeline event
    event_data = TimelineEventCreate(
        event_type=parsed["event_type"],
        event_date=datetime.utcnow(),
        title=parsed["title"],
        description=parsed["description"],
        payload=parsed["payload"]
    )
    create_timeline_event(db, current_user.id, event_data)
    
    # Mark as committed
    voice_log.is_committed = True
    db.commit()
    db.refresh(voice_log)
    
    # Recalculate score dynamically
    calculate_health_metrics(db, current_user.id)
    
    return voice_log
