from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil

from app.core.database import get_db
from app.features.voice.schemas import VoiceJournalResponse
from app.features.voice.tasks import process_audio_journal_task

router = APIRouter(prefix="/voice", tags=["Voice Health Journal"])

UPLOAD_DIR = "/tmp/vitalpath_audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/journal", response_model=VoiceJournalResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_voice_journal(
    user_id: int,
    language: str = Form("en"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploads user voice recording to be transcribed and structured into events asynchronously."""
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Offload processing to background Celery worker
    process_audio_journal_task.delay(user_id, file_path, language)
    
    # Return immediate 202 Accepted status
    return VoiceJournalResponse(
        id=0,
        user_id=user_id,
        audio_file_path=file_path,
        transcription="Processing speech in background...",
        language=language,
        detected_intent="Pending",
        created_at=datetime.utcnow()
    )
