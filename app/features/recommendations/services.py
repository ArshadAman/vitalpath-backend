import logging
from sqlalchemy.orm import Session

from app.features.recommendations.schemas import ExercisePlan, NutritionTargets, PreventiveTests, RecommendationResponse
from app.features.profile.services import get_health_profile
from app.features.score.services import get_latest_health_score
from app.features.tracking.models import ActivityLog, SleepLog, WeightLog, BPLog
from app.features.reports.models import MedicalReport
from app.features.recommendations.ml_recommender import get_best_match_recommendations

logger = logging.getLogger(__name__)

def generate_recommendations(db: Session, user_id: int) -> RecommendationResponse:
    """
    Generates personalized diet, exercise, and testing guidelines using a Content-Based
    Filtering Cosine Similarity Engine over vector spaces.
    """
    # 1. Fetch user profile & demographics
    profile = get_health_profile(db, user_id)
    
    # Establish baseline defaults
    weight_kg = 70.0
    actual_age = 30
    gender = "male"
    smoking = "never"
    exercise_freq = "active"
    diet = "balanced"
    goal = "wellness"
    calorie_target = 2000.0
    water_target = 3000.0
    
    if profile:
        weight_kg = profile.weight or 70.0
        gender = getattr(profile, "gender", "male") or "male"
        smoking = profile.smoking_status or "never"
        exercise_freq = profile.exercise_frequency or "active"
        diet = (profile.diet_type or "balanced").lower()
        goal = (profile.health_goal or "wellness").lower()
        calorie_target = float(profile.calorie_target or 2000.0)
        water_target = float(profile.water_target or 3000.0)
        if profile.age:
            actual_age = profile.age

    # 2. Fetch latest telemetry averages
    # Avg steps (default to 7500)
    steps_logs = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).all()
    avg_steps = sum(l.steps for l in steps_logs) / len(steps_logs) if steps_logs else (8000.0 if exercise_freq != "rarely" else 3000.0)

    # Avg sleep (default to 7.2 hrs)
    sleep_logs = db.query(SleepLog).filter(SleepLog.user_id == user_id).all()
    avg_sleep = sum(l.duration_hours for l in sleep_logs) / len(sleep_logs) if sleep_logs else 7.5

    # Latest BP
    recent_bp = db.query(BPLog).filter(BPLog.user_id == user_id).order_by(BPLog.date.desc()).first()
    sbp_val = float(recent_bp.systolic) if recent_bp else 120.0

    # Latest weight
    recent_weight = db.query(WeightLog).filter(WeightLog.user_id == user_id).order_by(WeightLog.date.desc()).first()
    if recent_weight:
        weight_kg = recent_weight.weight_kg

    # 3. Fetch latest lab biomarkers from medical reports
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

    hba1c_val = biomarkers.get("HbA1c", 5.4)
    chol_val = biomarkers.get("Total Cholesterol", 180.0)
    vit_d3_val = biomarkers.get("Vitamin D3", 40.0)
    hb_val = biomarkers.get("Hemoglobin", 14.5)

    # 4. Invoke Cosine Similarity vector recommender
    matched_exercise, matched_nutrition, matched_tests = get_best_match_recommendations(
        goal=goal,
        diet=diet,
        weight=weight_kg,
        sbp=sbp_val,
        hba1c=hba1c_val,
        cholesterol=chol_val,
        steps=avg_steps,
        sleep=avg_sleep,
        vit_d3=vit_d3_val,
        hemoglobin=hb_val
    )

    # 5. Hydrate Pydantic response structures
    # Calculate protein requirements dynamically based on matched macro coefficients
    rec_protein = weight_kg * matched_nutrition["protein_factor"]
    rec_calories = calorie_target + matched_nutrition["calorie_adjustment"]

    # Limit extreme calorie target drops
    rec_calories = max(1200.0, rec_calories)

    # Add clinical custom meal markers (sodium restriction, fiber addition) based on inputs
    suggestions = list(matched_nutrition["meal_suggestions"])
    nutrition_rationale = matched_nutrition["rationale"]

    if sbp_val >= 130:
        suggestions.append("Sodium restriction: Restrict sodium strictly below 2,000mg/day to support BP recovery.")
        nutrition_rationale += " DASH protocol guidelines appended."
    if chol_val >= 200:
        suggestions.append("Soluble fiber: Target 10g of daily soluble fiber to bind gut bile acids.")
        nutrition_rationale += " Lipid clearing elements integrated."

    exercise_plan = ExercisePlan(
        plan_name=matched_exercise["plan_name"],
        frequency=matched_exercise["frequency"],
        routines=matched_exercise["routines"],
        rationale=matched_exercise["rationale"]
    )

    nutrition_targets = NutritionTargets(
        protein_target_g=round(rec_protein, 1),
        water_target_l=round(water_target / 1000.0, 1),
        calorie_target_kcal=round(rec_calories, 0),
        meal_suggestions=suggestions,
        rationale=nutrition_rationale
    )

    preventive_tests = PreventiveTests(
        recommended_tests=matched_tests["recommended_tests"],
        frequency=matched_tests["frequency"],
        rationale=matched_tests["rationale"]
    )

    logger.info(f"Vector Space similarity recommendations matched for user {user_id}")
    return RecommendationResponse(
        exercise=exercise_plan,
        nutrition=nutrition_targets,
        preventive_tests=preventive_tests
    )
