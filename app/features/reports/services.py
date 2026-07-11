from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os
import re
import pdfplumber
from app.features.reports.models import MedicalReport

# Whitelist of clinical biomarkers and their matching regex patterns
CLINICAL_WHITELIST = {
    "HbA1c": {
        "patterns": [r"hba1c", r"glycated\s+hemoglobin", r"hb\s*a1c"],
        "unit": "%",
        "reference_range": "< 5.7%"
    },
    "LDL Cholesterol": {
        "patterns": [r"ldl", r"ldl\s+cholesterol", r"low\s+density\s+lipoprotein"],
        "unit": "mg/dL",
        "reference_range": "< 100 mg/dL"
    },
    "HDL Cholesterol": {
        "patterns": [r"hdl", r"hdl\s+cholesterol", r"high\s+density\s+lipoprotein"],
        "unit": "mg/dL",
        "reference_range": "> 40 mg/dL"
    },
    "Fasting Blood Sugar": {
        "patterns": [r"glucose", r"fasting\s+blood\s+sugar", r"fasting\s+glucose", r"sugar"],
        "unit": "mg/dL",
        "reference_range": "70 - 99 mg/dL"
    },
    "Vitamin D3": {
        "patterns": [r"vitamin\s+d", r"vit\s+d", r"25-oh\s+vitamin\s+d"],
        "unit": "ng/mL",
        "reference_range": "30.0 - 100.0 ng/mL"
    },
    "Triglycerides": {
        "patterns": [r"triglycerides", r"trig"],
        "unit": "mg/dL",
        "reference_range": "< 150 mg/dL"
    },
    "Total Cholesterol": {
        "patterns": [r"total\s+cholesterol", r"cholest"],
        "unit": "mg/dL",
        "reference_range": "< 200 mg/dL"
    },
    "Thyroid TSH": {
        "patterns": [r"tsh", r"thyroid\s*stimulating\s*hormone"],
        "unit": "uIU/mL",
        "reference_range": "0.4 - 4.0 uIU/mL"
    },
    "Creatinine": {
        "patterns": [r"creatinine", r"creat"],
        "unit": "mg/dL",
        "reference_range": "0.6 - 1.2 mg/dL"
    },
    "Hemoglobin": {
        "patterns": [r"hemoglobin", r"hemo", r"hgb"],
        "unit": "g/dL",
        "reference_range": "13.0 - 16.5 g/dL"
    },
    "WBC Count": {
        "patterns": [r"wbc\s+count", r"wbc", r"white\s+blood\s+cells"],
        "unit": "/cmm",
        "reference_range": "4000 - 10000 /cmm"
    },
    "RBC Count": {
        "patterns": [r"rbc\s+count", r"rbc", r"red\s+blood\s+cells"],
        "unit": "million/cmm",
        "reference_range": "4.5 - 5.5 million/cmm"
    },
    "Hematocrit": {
        "patterns": [r"hematocrit", r"hct"],
        "unit": "%",
        "reference_range": "40 - 49 %"
    },
    "Packed Cell Volume (PCV)": {
        "patterns": [r"packed\s+cell\s+volume", r"pcv"],
        "unit": "%",
        "reference_range": "40 - 50 %"
    },
    "MCV": {
        "patterns": [r"mcv", r"mean\s+corpuscular\s+volume"],
        "unit": "fL",
        "reference_range": "83 - 101 fL"
    },
    "MCH": {
        "patterns": [r"mch", r"mean\s+corpuscular\s+hemoglobin"],
        "unit": "pg",
        "reference_range": "27.1 - 32.5 pg"
    },
    "MCHC": {
        "patterns": [r"mchc"],
        "unit": "g/dL",
        "reference_range": "32.5 - 36.7 g/dL"
    },
    "RDW CV": {
        "patterns": [r"rdw\s+cv", r"rdw"],
        "unit": "%",
        "reference_range": "11.6 - 14 %"
    },
    "Platelet Count": {
        "patterns": [r"platelet\s+count", r"platelets", r"plt"],
        "unit": "/cmm",
        "reference_range": "150000 - 410000 /cmm"
    },
    "MPV": {
        "patterns": [r"mpv", r"mean\s+platelet\s+volume"],
        "unit": "fL",
        "reference_range": "7.5 - 10.3 fL"
    },
    "ESR": {
        "patterns": [r"esr", r"erythrocyte\s+sedimentation\s+rate"],
        "unit": "mm/1hr",
        "reference_range": "0 - 14 mm/1hr"
    }
}

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
        status="pending",
        metrics=[]
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

def update_report_metrics(db: Session, report_id: int, metrics_list: List[dict]) -> Optional[MedicalReport]:
    """Saves manually corrected metrics back to the report's JSONB field."""
    report = get_medical_report(db, report_id)
    if report:
        report.metrics = metrics_list
        db.commit()
        db.refresh(report)
    return report

def simulate_ocr_extraction(file_path: str) -> List[dict]:
    """Scrapes raw text from digital PDFs and preprocessed images, extracting ONLY whitelisted clinical parameters."""
    extracted_text = ""
    files_to_scan = []
    
    if os.path.isdir(file_path):
        for f in os.listdir(file_path):
            files_to_scan.append(os.path.join(file_path, f))
    else:
        files_to_scan.append(file_path)
        
    for path in files_to_scan:
        if path.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
            except Exception as e:
                print(f"pdfplumber error on file {path}: {e}")
        elif path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            try:
                from PIL import Image, ImageEnhance, ImageFilter
                import pytesseract
                
                # Load image asset
                raw_img = Image.open(path)
                # Convert to grayscale to remove color channel noise
                gray_img = raw_img.convert('L')
                # Scale resolution by 2.5x to enlarge small print characters cleanly
                new_size = (int(gray_img.width * 2.5), int(gray_img.height * 2.5))
                resized_img = gray_img.resize(new_size, Image.Resampling.LANCZOS)
                # Elevate contrast to sharpen anti-aliased character boundaries
                enhancer = ImageEnhance.Contrast(resized_img)
                high_contrast_img = enhancer.enhance(2.5)
                # Sharpen to make numeric digits (like 5 vs 8) highly distinct
                sharpened_img = high_contrast_img.filter(ImageFilter.SHARPEN)
                
                # Parse layout-resilient text lines
                img_text = pytesseract.image_to_string(sharpened_img, config="--psm 6")
                if img_text:
                    extracted_text += img_text + "\n"
            except Exception as e:
                print(f"pytesseract error on file {path}: {e}")
                
    metrics = []
    if extracted_text:
        text_lower = extracted_text.lower()
        
        for metric_name, info in CLINICAL_WHITELIST.items():
            for pattern in info["patterns"]:
                # Match the parameter name followed by a numeric value strictly on the same line
                match = re.search(pattern + r"[^\d\.\n]*?(\d+\.?\d*)", text_lower)
                if match:
                    metrics.append({
                        "test_name": metric_name,
                        "value": float(match.group(1)),
                        "unit": info["unit"],
                        "reference_range": info["reference_range"],
                        "test_date": datetime.utcnow().isoformat()
                    })
                    # Found a match for this metric, stop checking other aliases
                    break
                    
    return metrics
