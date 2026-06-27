from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExtractedMetricBase(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    test_date: datetime

class ExtractedMetricCreate(ExtractedMetricBase):
    pass

class ExtractedMetricUpdate(BaseModel):
    test_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: Optional[datetime] = None

class ExtractedMetricResponse(ExtractedMetricBase):
    id: int
    report_id: int

    class Config:
        from_attributes = True

class MedicalReportResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    status: str
    uploaded_at: datetime
    metrics: List[ExtractedMetricResponse] = []

    class Config:
        from_attributes = True
