from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from app.core.database import get_db
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.timeline.models import TimelineEvent
from app.features.reports.schemas import MedicalReportResponse, ExtractedMetricSchema
from app.features.reports.services import (
    create_report_entry, get_medical_report, get_user_reports, update_report_metrics
)
from app.features.reports.tasks import process_report_ocr_task

router = APIRouter(prefix="/reports", tags=["Medical Reports"])

UPLOAD_DIR = "/workspace/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=MedicalReportResponse, status_code=status.HTTP_201_CREATED)
def upload_report(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Receives one or more binary report uploads (supporting multi-page reports) and schedules background OCR."""
    import uuid
    report_uuid = str(uuid.uuid4())
    report_dir = os.path.join(UPLOAD_DIR, f"{current_user.id}_{report_uuid}")
    os.makedirs(report_dir, exist_ok=True)
    
    first_filename = "report_document"
    if files:
        first_filename = files[0].filename
        
    for file in files:
        file_path = os.path.join(report_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    db_report = create_report_entry(db, current_user.id, first_filename, report_dir)
    
    # Schedule celery OCR extraction task
    process_report_ocr_task.delay(db_report.id)
    
    return db_report

@router.get("", response_model=List[MedicalReportResponse])
def read_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves all reports uploaded by user."""
    return get_user_reports(db, current_user.id)

@router.get("/{report_id}", response_model=MedicalReportResponse)
def read_report(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Gets details for single report and its metrics."""
    report = get_medical_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical report not found")
    return report

@router.put("/{report_id}/metrics", response_model=MedicalReportResponse)
def update_metrics(report_id: int, updated_metrics: List[ExtractedMetricSchema], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Allows manual correction of OCR parameters stored inside the report's JSONB metrics array."""
    report = get_medical_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical report not found")
        
    # Serialize the validation schema array directly to the report record in JSON-compatible formats
    serialized = [m.model_dump(mode="json") for m in updated_metrics]
    updated = update_report_metrics(db, report_id, serialized)
    return updated

from fastapi.responses import FileResponse

@router.get("/{report_id}/download")
def download_report_file(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Downloads the raw uploaded medical report file (or first page if multi-page)."""
    report = get_medical_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical report not found")
        
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="File does not exist on disk")
        
    target_path = report.file_path
    if os.path.isdir(report.file_path):
        files = sorted(os.listdir(report.file_path))
        if not files:
            raise HTTPException(status_code=404, detail="No files in report folder")
        target_path = os.path.join(report.file_path, files[0])
        
    return FileResponse(target_path, filename=report.file_name)

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int, 
    delete_timeline: bool = False, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Deletes a medical report, and optionally its corresponding health timeline event."""
    report = get_medical_report(db, report_id)
    if not report or report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Medical report not found")
        
    # Delete associated timeline event if requested
    if delete_timeline:
        events = db.query(TimelineEvent).filter(TimelineEvent.user_id == current_user.id).all()
        for event in events:
            payload = event.payload or {}
            if str(payload.get("report_id")) == str(report_id):
                db.delete(event)
                
    # Clean up files from disk
    if report.file_path and os.path.exists(report.file_path):
        try:
            if os.path.isdir(report.file_path):
                shutil.rmtree(report.file_path)
            else:
                os.remove(report.file_path)
        except Exception as e:
            print(f"Error removing report files from disk: {e}")
            
    db.delete(report)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
