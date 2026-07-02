from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from app.core.database import get_db
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.reports.models import ExtractedMetric
from app.features.reports.schemas import MedicalReportResponse, ExtractedMetricResponse, ExtractedMetricUpdate
from app.features.reports.services import (
    create_report_entry, get_medical_report, get_user_reports, update_extracted_metric
)
from app.features.reports.tasks import process_report_ocr_task

router = APIRouter(prefix="/reports", tags=["Medical Reports"])

UPLOAD_DIR = "/tmp/vitalpath_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=MedicalReportResponse, status_code=status.HTTP_201_CREATED)
def upload_report(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Receives binary report uploads and schedules background OCR task."""
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_report = create_report_entry(db, current_user.id, file.filename, file_path)
    
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

@router.put("/metrics/{metric_id}", response_model=ExtractedMetricResponse)
def correct_metric(metric_id: int, update_data: ExtractedMetricUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """API for users to perform manual correction of erroneous OCR outputs."""
    # Enforce data validation so that metrics belong to the authenticated user's report
    metric = db.query(ExtractedMetric).filter(ExtractedMetric.id == metric_id).first()
    if not metric or metric.report.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Metric not found")
        
    updated = update_extracted_metric(db, metric_id, update_data)
    return updated
