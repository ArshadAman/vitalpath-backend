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

router = APIRouter(prefix="/voice", tags=["Voice Health Journal"])

UPLOAD_DIR = "/tmp/vitalpath_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/journal", response_model=VoiceJournalResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_voice_journal(
    language: str = Form("en"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Uploads user voice recording to be transcribed and structured into events asynchronously."""
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Offload processing to background Celery worker
    process_audio_journal_task.delay(current_user.id, file_path, language)
    
    # Return immediate 202 Accepted status
    return VoiceJournalResponse(
        id=0,
        user_id=current_user.id,
        audio_file_path=file_path,
        transcription="Processing speech in background...",
        language=language,
        detected_intent="Pending",
        created_at=datetime.utcnow()
    )
