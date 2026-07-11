from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExtractedMetricSchema(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    test_date: datetime

class MedicalReportResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    status: str
    uploaded_at: datetime
    metrics: List[ExtractedMetricSchema] = []

    class Config:
        from_attributes = True
