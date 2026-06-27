from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.features.reports.models import MedicalReport, ExtractedMetric
from app.features.reports.schemas import ExtractedMetricCreate, ExtractedMetricUpdate

def get_medical_report(db: Session, report_id: int) -> Optional[MedicalReport]:
    """Retrieves report entry by ID."""
    return db.query(MedicalReport).filter(MedicalReport.id == report_id).first()

def get_user_reports(db: Session, user_id: int) -> List[MedicalReport]:
    """Retrieves all reports uploaded by a user."""
    return db.query(MedicalReport).filter(MedicalReport.user_id == user_id).all()

def create_report_entry(db: Session, user_id: int, file_name: str, file_path: str) -> MedicalReport:
    """Creates a new database record for a report."""
    db_report = MedicalReport(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        status="pending"
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def update_report_status(db: Session, report_id: int, status: str) -> Optional[MedicalReport]:
    """Updates processing state of report."""
    report = get_medical_report(db, report_id)
    if report:
        report.status = status
        db.commit()
        db.refresh(report)
    return report

def add_extracted_metric(db: Session, report_id: int, metric_data: ExtractedMetricCreate) -> ExtractedMetric:
    """Inserts a newly parsed metric into database."""
    db_metric = ExtractedMetric(
        report_id=report_id,
        **metric_data.model_dump()
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

def update_extracted_metric(db: Session, metric_id: int, update_data: ExtractedMetricUpdate) -> Optional[ExtractedMetric]:
    """Allows manual override of extracted OCR metrics."""
    metric = db.query(ExtractedMetric).filter(ExtractedMetric.id == metric_id).first()
    if not metric:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(metric, key, value)
        
    db.commit()
    db.refresh(metric)
    return metric

def simulate_ocr_extraction(file_path: str) -> List[ExtractedMetricCreate]:
    """Mock OCR helper returning static blood panel tests."""
    return [
        ExtractedMetricCreate(
            test_name="HbA1c",
            value=5.9,
            unit="%",
            reference_range="< 5.7%",
            test_date=datetime.utcnow()
        ),
        ExtractedMetricCreate(
            test_name="LDL",
            value=135.0,
            unit="mg/dL",
            reference_range="< 100 mg/dL",
            test_date=datetime.utcnow()
        ),
        ExtractedMetricCreate(
            test_name="HDL",
            value=45.0,
            unit="mg/dL",
            reference_range="> 40 mg/dL",
            test_date=datetime.utcnow()
        )
    ]
