import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.features.score.models import HealthScoreLog
from app.features.profile.services import get_health_profile
from app.features.tracking.models import ActivityLog, SleepLog, WeightLog, BPLog
from app.features.timeline.models import TimelineEvent
from app.features.reports.models import MedicalReport
from app.features.score.ml_engine import predict_biological_age_offset_knn, predict_health_score_regression

logger = logging.getLogger(__name__)

def calculate_health_metrics(db: Session, user_id: int) -> HealthScoreLog:
    """
    Doctor & Dietitian grade health score & biological age calculator.
    Dynamically aggregates logs, profiles, and medical report biomarkers,
    applies goal-specific weights, and returns a detailed factors breakdown.
    """
    # 1. Fetch profile & calibrate baselines
    profile = get_health_profile(db, user_id)
    
    actual_age = 30
    gender = "male"
    height_cm = 175.0
    smoking = "never"
    alcohol = "none"
    goal = "wellness"
    
    if profile:
        if getattr(profile, "age", None):
            actual_age = profile.age
        elif profile.date_of_birth:
            actual_age = (datetime.utcnow() - profile.date_of_birth).days // 365
        gender = getattr(profile, "gender", "male") or "male"
        height_cm = getattr(profile, "height", 175.0) or 175.0
        smoking = profile.smoking_status or "never"
        alcohol = profile.alcohol_consumption or "none"
        goal = getattr(profile, "health_goal", "wellness") or "wellness"
        
    goal = goal.lower()
    
    # 2. Fetch latest lifestyle metrics
    recent_bp = db.query(BPLog).filter(BPLog.user_id == user_id).order_by(BPLog.date.desc()).first()
    recent_weight = db.query(WeightLog).filter(WeightLog.user_id == user_id).order_by(WeightLog.date.desc()).first()
    
    # Average last 3 days for steps & sleep to smooth fluctuations
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    
    activity_logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.date >= three_days_ago
    ).all()
    avg_steps = sum(log.steps for log in activity_logs) / len(activity_logs) if activity_logs else 6000
    
    sleep_logs = db.query(SleepLog).filter(
        SleepLog.user_id == user_id,
        SleepLog.date >= three_days_ago
    ).all()
    avg_sleep = sum(log.duration_hours for log in sleep_logs) / len(sleep_logs) if sleep_logs else 7.5
    
    # Hydration tracking from timeline
    hydration_events = db.query(TimelineEvent).filter(
        TimelineEvent.user_id == user_id,
        TimelineEvent.event_date >= (datetime.utcnow() - timedelta(hours=24)),
        (TimelineEvent.event_type == "hydration") | 
        ((TimelineEvent.event_type == "logs") & (TimelineEvent.title.ilike("%water%") | TimelineEvent.title.ilike("%hydration%")))
    ).all()
    
    total_water_ml = 0
    for ev in hydration_events:
        val_str = ev.payload.get("value", "") if ev.payload else ""
        match = re.search(r"(\d+)", str(val_str))
        if match:
            val = int(match.group(1))
            if "glass" in str(val_str).lower():
                total_water_ml += val * 250
            else:
                # assume ml directly
                total_water_ml += val
                
    hydration_glasses = total_water_ml / 250.0 if total_water_ml > 0 else 6.0

    # 3. Fetch latest lab biomarkers from verified reports
    reports = db.query(MedicalReport).filter(
        MedicalReport.user_id == user_id,
        MedicalReport.status == "completed"
    ).order_by(MedicalReport.uploaded_at.desc()).all()
    
    biomarkers = {}
    for r in reports:
        if r.metrics:
            for m in r.metrics:
                name = m.get("test_name")
                val = m.get("value")
                if name and val is not None and name not in biomarkers:
                    biomarkers[name] = float(val)

    # Extract specific biomarkers
    hba1c = biomarkers.get("HbA1c")
    glucose = biomarkers.get("Fasting Blood Sugar")
    total_chol = biomarkers.get("Total Cholesterol")
    vit_d3 = biomarkers.get("Vitamin D3")
    hemoglobin = biomarkers.get("Hemoglobin")
    wbc = biomarkers.get("WBC Count")
    esr = biomarkers.get("ESR")

    # 4. Process dimensions and build factor details
    details = []

    # A. Blood Pressure
    bp_status = "optimal"
    bp_score = 0
    bp_age = 0.0
    bp_reason = "Optimal cardiovascular compliance; low arterial shear stress."
    bp_tip = "Maintain current sodium limit and support with aerobic physical activity."
    
    if recent_bp:
        sys = recent_bp.systolic
        dia = recent_bp.diastolic
        bp_val_str = f"{sys}/{dia} mmHg"
        if sys >= 140 or dia >= 90:
            bp_status = "critical"
            bp_score = -15
            bp_age = 3.0
            bp_reason = "Elevated blood pressure indicates systemic vascular resistance and cardiorenal strain."
            bp_tip = "Strict DASH diet: Cap dietary sodium under 1,500mg daily, eliminate trans fats, and optimize potassium intake (greens, bananas)."
        elif sys >= 120 or dia >= 80:
            bp_status = "warning"
            bp_score = -6
            bp_age = 1.0
            bp_reason = "Elevated BP indicates prehypertension and mild endothelial stress."
            bp_tip = "Increase daily dietary potassium (spinach, avocados) and restrict sodium intake to under 2,000mg per day."
    else:
        bp_val_str = "No recent records"
        
    details.append({
        "name": "Blood Pressure",
        "status": bp_status,
        "value": bp_val_str,
        "score_impact": bp_score,
        "age_impact": bp_age,
        "reason": bp_reason,
        "tip": bp_tip
    })

    # B. Glycemic Health (HbA1c)
    hba1c_status = "optimal"
    hba1c_score = 0
    hba1c_age = 0.0
    hba1c_reason = "Healthy long-term glycemic management; minimal systemic glycation."
    hba1c_tip = "Continue focusing on low glycemic load complex carbohydrates and fiber."
    
    if hba1c is not None:
        hba1c_val_str = f"{hba1c}%"
        if hba1c >= 6.5:
            hba1c_status = "critical"
            hba1c_score = -20
            hba1c_age = 5.0
            hba1c_reason = "Glycated hemoglobin levels denote active diabetes, driving microvascular strain."
            hba1c_tip = "Eliminate simple starches and refined sugars. Integrate high-fiber foods (35g+ daily) and consult your doctor."
        elif hba1c >= 5.7:
            hba1c_status = "warning"
            hba1c_score = -8
            hba1c_age = 2.0
            hba1c_reason = "Fasting glucose markers indicate prediabetic insulin resistance."
            hba1c_tip = "Stabilize glucose spikes: Pair carbs with protein/fats and walk 10 minutes immediately after primary meals."
    else:
        hba1c_val_str = "No recent labs"
        
    details.append({
        "name": "Glycemic (HbA1c)",
        "status": hba1c_status,
        "value": hba1c_val_str,
        "score_impact": hba1c_score,
        "age_impact": hba1c_age,
        "reason": hba1c_reason,
        "tip": hba1c_tip
    })

    # C. Fasting Glucose
    gluc_status = "optimal"
    gluc_score = 0
    gluc_age = 0.0
    gluc_reason = "Fasting blood sugar is in the healthy metabolic range."
    gluc_tip = "Continue utilizing fibrous foods to buffer insulin response."
    
    if glucose is not None:
        gluc_val_str = f"{glucose} mg/dL"
        if glucose >= 126:
            gluc_status = "critical"
            gluc_score = -15
            gluc_age = 3.0
            gluc_reason = "Fasting glucose exceeds diabetic clinical thresholds."
            gluc_tip = "Restrict simple carbohydrate/sugar intake, lift weights to clear glycogen, and consult a physician."
        elif glucose >= 100:
            gluc_status = "warning"
            gluc_score = -6
            gluc_age = 1.0
            gluc_reason = "Impaired fasting glucose indicates insulin clearing resistance."
            gluc_tip = "Adopt a low glycemic index diet. Focus on dietary magnesium (seeds, leafy greens) to support cell receptors."
    else:
        gluc_val_str = "No recent labs"
        
    details.append({
        "name": "Fasting Glucose",
        "status": gluc_status,
        "value": gluc_val_str,
        "score_impact": gluc_score,
        "age_impact": gluc_age,
        "reason": gluc_reason,
        "tip": gluc_tip
    })

    # D. BMI & Body Mass
    bmi_status = "optimal"
    bmi_score = 0
    bmi_age = 0.0
    bmi_reason = "Healthy body mass index ratio."
    bmi_tip = "Keep up current caloric balance matching daily active energy burn."
    
    if recent_weight:
        weight_kg = recent_weight.weight_kg
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m * height_m)
        bmi_val_str = f"{bmi:.1f} kg/m²"
        
        if bmi >= 30.0:
            bmi_status = "critical"
            bmi_score = -12
            bmi_age = 3.0
            bmi_reason = "Clinical obesity drives chronic vascular inflammation and visceral adiposity."
            bmi_tip = "Create moderate caloric deficit (300-500 kcal) with high protein density (1.6g/kg) and resistance training."
        elif bmi >= 25.0:
            bmi_status = "warning"
            bmi_score = -5
            bmi_age = 1.0
            bmi_reason = "Overweight body mass slightly elevations metabolic work."
            bmi_tip = "Reduce liquid calories and simple sugars, and increase fiber volume to promote healthy satiety."
        elif bmi < 18.5:
            bmi_status = "warning"
            bmi_score = -5
            bmi_age = 1.0
            bmi_reason = "Underweight BMI indicates risk of lean mass loss or nutrient deficiencies."
            bmi_tip = "Focus on healthy caloric surpluses with calorie-dense fats (nuts, avocados, clean oils) and strength training."
    else:
        bmi_val_str = "No weight logged"
        
    details.append({
        "name": "Body Mass Index (BMI)",
        "status": bmi_status,
        "value": bmi_val_str,
        "score_impact": bmi_score,
        "age_impact": bmi_age,
        "reason": bmi_reason,
        "tip": bmi_tip
    })

    # E. Total Cholesterol
    chol_status = "optimal"
    chol_score = 0
    chol_age = 0.0
    chol_reason = "Healthy lipid profile reduces risk of arterial plaque buildup."
    chol_tip = "Continue diets rich in monounsaturated fats (olive oil) and soluble fiber."
    
    if total_chol is not None:
        chol_val_str = f"{total_chol} mg/dL"
        if total_chol >= 240:
            chol_status = "critical"
            chol_score = -10
            chol_age = 2.0
            chol_reason = "Hypercholesterolemia increases plaque formulation rate."
            chol_tip = "Strictly limit saturated fats. Supplement with omega-3s and consider plant sterols/stanols."
        elif total_chol >= 200:
            chol_status = "warning"
            chol_score = -4
            chol_age = 1.0
            chol_reason = "Borderline lipid elevation represents early arterial risk vectors."
            chol_tip = "Soluble fiber protocol: Consume beta-glucans (oats) daily to bind and clear cholesterol in the gut."
    else:
        chol_val_str = "No recent labs"
        
    details.append({
        "name": "Total Cholesterol",
        "status": chol_status,
        "value": chol_val_str,
        "score_impact": chol_score,
        "age_impact": chol_age,
        "reason": chol_reason,
        "tip": chol_tip
    })

    # F. Vitamin D3
    d3_status = "optimal"
    d3_score = 0
    d3_age = 0.0
    d3_reason = "Optimal steroid precursor levels support calcium binding and immunity."
    d3_tip = "Maintain safe solar exposure or current maintenance supplementation."
    
    if vit_d3 is not None:
        d3_val_str = f"{vit_d3} ng/mL"
        if vit_d3 < 20:
            d3_status = "critical"
            d3_score = -12
            d3_age = 2.0
            d3_reason = "Severe Vitamin D3 deficiency degrades bone density and cellular immune response."
            d3_tip = "High-dose clinical supplementation: Target 5,000 IU daily alongside Vitamin K2 to ensure calcium goes to bones, not arteries."
        elif vit_d3 < 30:
            d3_status = "warning"
            d3_score = -5
            d3_age = 1.0
            d3_reason = "Mild Vitamin D3 insufficiency reduces systemic immune resilience."
            d3_tip = "Supplement with 2,000 IU Vitamin D3 daily, paired with a fat-rich meal to maximize bioavailability."
    else:
        d3_val_str = "No recent labs"
        
    details.append({
        "name": "Vitamin D3",
        "status": d3_status,
        "value": d3_val_str,
        "score_impact": d3_score,
        "age_impact": d3_age,
        "reason": d3_reason,
        "tip": d3_tip
    })

    # G. Hemoglobin
    hemo_status = "optimal"
    hemo_score = 0
    hemo_age = 0.0
    hemo_reason = "Optimal red blood cell count supports cellular oxygen transport."
    hemo_tip = "Maintain intake of iron co-factors (vitamin C, B12) in diet."
    
    if hemoglobin is not None:
        hemo_val_str = f"{hemoglobin} g/dL"
        low_limit = 13.5 if gender == "male" else 12.0
        if hemoglobin < low_limit:
            hemo_status = "critical"
            hemo_score = -10
            hemo_age = 2.0
            hemo_reason = "Low hemoglobin denotes clinical anemia, compromising oxygen carrying capacity."
            
            diet_pref = (profile.diet_type or "balanced").lower() if profile else "balanced"
            if diet_pref in ["vegan", "vegetarian"]:
                hemo_tip = "Erythropoiesis support: Consume non-heme iron sources (spinach, lentils, pumpkin seeds) paired with Vitamin C to enhance absorption, and screen for B12."
            else:
                hemo_tip = "Erythropoiesis support: Consume heme iron (lean meats) or non-heme iron paired with Vitamin C, and screen for Folate/B12."
    else:
        hemo_val_str = "No recent labs"
        
    details.append({
        "name": "Hemoglobin",
        "status": hemo_status,
        "value": hemo_val_str,
        "score_impact": hemo_score,
        "age_impact": hemo_age,
        "reason": hemo_reason,
        "tip": hemo_tip
    })

    # H. Inflammatory Markers (WBC / ESR)
    inf_status = "optimal"
    inf_score = 0
    inf_age = 0.0
    inf_reason = "Inflammatory markers are quiet, indicating absence of chronic systemic stress."
    inf_tip = "Support with antioxidant polyphenols (berries, green tea) and stress management."
    
    inf_vals = []
    if wbc is not None:
        inf_vals.append(f"WBC: {wbc:.0f}")
        if wbc > 11000:
            inf_status = "warning"
            inf_score -= 8
            inf_age += 1.0
            inf_reason = "Elevated WBC counts denote active immune activation or acute inflammation."
            inf_tip = "Prioritize zinc, vitamin C, and anti-inflammatory spices (ginger, garlic) while focusing on rest."
            
    if esr is not None:
        inf_vals.append(f"ESR: {esr:.0f}")
        limit = 15 if gender == "male" else 20
        if esr > limit:
            inf_status = "warning" if inf_status == "optimal" else "critical"
            inf_score -= 8
            inf_age += 1.0
            inf_reason = "Elevated ESR indicates ongoing systemic inflammation."
            inf_tip = "Incorporate high-dose omega-3 fatty acids (EPA/DHA) and curcumin, and optimize gut barrier integrity."
            
    inf_val_str = ", ".join(inf_vals) if inf_vals else "No recent labs"
    
    details.append({
        "name": "Inflammation (WBC/ESR)",
        "status": inf_status,
        "value": inf_val_str,
        "score_impact": inf_score,
        "age_impact": inf_age,
        "reason": inf_reason,
        "tip": inf_tip
    })

    # I. Daily Steps
    step_status = "optimal"
    step_score = 5
    step_age = -1.0
    step_reason = "Excellent steps baseline clears postprandial glucose and stimulates arterial nitric oxide."
    step_tip = "Maintain active threshold to support heart health and fat metabolism."
    
    if avg_steps < 4000:
        step_status = "critical"
        step_score = -12
        step_age = 3.0
        step_reason = "Sedentary walking base reduces vascular compliance and insulin sensitivity."
        step_tip = "Vascular compliance: Set hourly standing goals and walk 10 minutes immediately after eating."
    elif avg_steps < 8000:
        step_status = "warning"
        step_score = -5
        step_age = 1.0
        step_reason = "Moderate step activity slightly limits cardiorespiratory protection."
        step_tip = "Aim to add 2,000 steps to your baseline by taking stairs and walking during phone calls."
        
    details.append({
        "name": "Physical Activity",
        "status": step_status,
        "value": f"{int(avg_steps):,} steps/day",
        "score_impact": step_score,
        "age_impact": step_age,
        "reason": step_reason,
        "tip": step_tip
    })

    # J. Sleep
    sleep_status = "optimal"
    sleep_score = 5
    sleep_age = -1.0
    sleep_reason = "Optimal sleep window supports glymphatic wash and cortisol reduction."
    sleep_tip = "Maintain consistent sleep/wake times and limit blue light screens before bed."
    
    if avg_sleep < 6.0:
        sleep_status = "critical"
        sleep_score = -12
        sleep_age = 2.0
        sleep_reason = "Severe sleep restriction spikes ghrelin/suppresses leptin, inducing sugar cravings and cortisol storage."
        sleep_tip = "Hormonal recovery: Spend 8 hours in bed. Consider magnesium bisglycinate and a screen-free wind-down."
    elif avg_sleep < 7.0 or avg_sleep > 9.5:
        sleep_status = "warning"
        sleep_score = -5
        sleep_age = 1.0
        sleep_reason = "Sub-optimal sleep window elevates stress hormones."
        sleep_tip = "Prioritize circadian rhythm: Get direct outdoor sunlight within 30 minutes of waking up."
        
    details.append({
        "name": "Sleep Architecture",
        "status": sleep_status,
        "value": f"{avg_sleep:.1f} hours/day",
        "score_impact": sleep_score,
        "age_impact": sleep_age,
        "reason": sleep_reason,
        "tip": sleep_tip
    })

    # K. Hydration (Water)
    hyd_status = "optimal"
    hyd_score = 3
    hyd_age = -0.5
    hyd_reason = "Optimal hydration reduces hematocrit viscosity and eases kidney filtration workload."
    hyd_tip = "Maintain steady water intake throughout the day with a marked bottle."
    
    if hydration_glasses < 5.0:
        hyd_status = "critical"
        hyd_score = -8
        hyd_age = 1.5
        hyd_reason = "Dehydration limits lipolysis (fat clearing) efficiency and raises cardiovascular strain."
        hyd_tip = "Drink at least 2.5L of water daily, adding trace minerals/electrolytes if performing physical activity."
    elif hydration_glasses < 8.0:
        hyd_status = "warning"
        hyd_score = -3
        hyd_age = 0.5
        hyd_reason = "Mild dehydration compromises metabolic waste clearing."
        hyd_tip = "Drink a full glass of water immediately upon waking and prior to starting meals."
        
    details.append({
        "name": "Hydration Status",
        "status": hyd_status,
        "value": f"{hydration_glasses:.1f} glasses/day",
        "score_impact": hyd_score,
        "age_impact": hyd_age,
        "reason": hyd_reason,
        "tip": hyd_tip
    })

    # L. Substances
    tox_status = "optimal"
    tox_score = 0
    tox_age = 0.0
    tox_reason = "Absence of toxic stress from tobacco supports arterial compliance."
    tox_tip = "Maintain smoke-free environments."
    
    if smoking == "active":
        tox_status = "critical"
        tox_score = -20
        tox_age = 5.0
        tox_reason = "Tobacco smoke causes endothelial inflammation, vasoconstriction, and arterial stiffening."
        tox_tip = "Nicotine cessation: Formulate a quit protocol, support with exercise, and load up on dietary antioxidants."
        
    if alcohol == "regular":
        tox_status = "critical" if tox_status == "optimal" else "critical"
        tox_score -= 10
        tox_age += 2.0
        tox_reason = "Regular alcohol intake increases liver workload and degrades intestinal lining barrier integrity."
        tox_tip = "Limit alcohol intake to under 2 drinks weekly, and support liver clearing pathways with milk thistle."
        
    tox_val_str = f"Smoke: {smoking.title()} | Alcohol: {alcohol.title()}"
    
    details.append({
        "name": "Toxicity Baseline",
        "status": tox_status,
        "value": tox_val_str,
        "score_impact": tox_score,
        "age_impact": tox_age,
        "reason": tox_reason,
        "tip": tox_tip
    })

    # 5. Apply Goal-Specific Weights
    # Calculate goal weighting scaling factors
    w_bp, w_hba1c, w_gluc, w_bmi, w_chol, w_d3, w_hemo, w_inf, w_step, w_sleep, w_hyd, w_tox = [1.0] * 12
    
    if goal == "weight_loss":
        w_bmi = 2.0
        w_sleep = 1.5
        w_step = 1.5
    elif goal == "longevity":
        w_bp = 1.8
        w_chol = 1.8
        w_tox = 1.8
    elif goal == "muscle_gain":
        w_sleep = 1.8
        w_d3 = 1.5
        # overweight is less penalized, underweight more penalized
        if recent_weight and (weight_kg / ((height_cm/100.0)**2)) < 18.5:
            w_bmi = 2.0
            
    # Apply weights in loop to build final deductions
    total_score_impact = 0
    total_age_impact = 0.0
    
    # Mapping table for weights
    weight_map = {
        "Blood Pressure": w_bp,
        "Glycemic (HbA1c)": w_hba1c,
        "Fasting Glucose": w_gluc,
        "Body Mass Index (BMI)": w_bmi,
        "Total Cholesterol": w_chol,
        "Vitamin D3": w_d3,
        "Hemoglobin": w_hemo,
        "Inflammation (WBC/ESR)": w_inf,
        "Physical Activity": w_step,
        "Sleep Architecture": w_sleep,
        "Hydration Status": w_hyd,
        "Toxicity Baseline": w_tox
    }
    
    # 5. ML Predictors Integration
    # Setup inputs for Multivariable Linear Regression & kNN algorithms
    sbp_val = 120.0
    if recent_bp:
        sbp_val = float(recent_bp.systolic)
        
    bmi_val = 22.5
    if recent_weight:
        height_m = height_cm / 100.0
        bmi_val = recent_weight.weight_kg / (height_m * height_m)
        
    hba1c_val = hba1c if hba1c is not None else 5.4
    smoking_val = 1.0 if smoking == "active" else 0.0
    alcohol_val = 1.0 if alcohol == "regular" else 0.0

    # Run Multivariable Linear Regression for Health Score
    ml_score = predict_health_score_regression(
        steps=avg_steps,
        sleep=avg_sleep,
        bmi=bmi_val,
        hba1c=hba1c_val,
        sbp=sbp_val,
        smoking=smoking_val,
        alcohol=alcohol_val
    )

    # Run k-Nearest Neighbors Regression for Bio Age Offset
    ml_age_offset = predict_biological_age_offset_knn(
        age=actual_age,
        steps=avg_steps,
        sleep=avg_sleep,
        bmi=bmi_val,
        hba1c=hba1c_val,
        sbp=sbp_val,
        smoking=smoking_val,
        alcohol=alcohol_val,
        k=3
    )

    # Apply goal-specific scaling factor on ML outputs
    goal_multiplier = 1.0
    if goal == "weight_loss" and bmi_val >= 25.0:
        goal_multiplier = 1.3
    elif goal == "longevity" and (sbp_val >= 130 or smoking_val > 0.5):
        goal_multiplier = 1.4

    final_score = int(100 - (100 - ml_score) * goal_multiplier)
    final_score = max(10, min(100, final_score))

    final_offset = ml_age_offset * goal_multiplier
    final_health_age = int(max(18, min(actual_age + 12, actual_age + final_offset)))

    # Check if we have verified lab report metrics
    is_lab_verified = len(biomarkers) > 0

    factors_payload = {
        "summary": {
            "score": final_score,
            "actual_age": actual_age,
            "biological_age": final_health_age,
            "net_offset": round(final_offset, 1),
            "goal": goal.title(),
            "is_lab_verified": is_lab_verified
        },
        "details": details
    }

    # 6. Save score log to database
    score_log = HealthScoreLog(
        user_id=user_id,
        score=final_score,
        health_age=final_health_age,
        factors=factors_payload
    )
    db.add(score_log)
    db.commit()
    db.refresh(score_log)
    
    logger.info(f"Health score calculated for user {user_id}: {final_score}/100 (Bio Age: {final_health_age})")
    return score_log

def get_latest_health_score(db: Session, user_id: int) -> Optional[HealthScoreLog]:
    """Queries the database for the most recent health score log entry."""
    return db.query(HealthScoreLog).filter(HealthScoreLog.user_id == user_id).order_by(HealthScoreLog.created_at.desc()).first()
