from sqlalchemy.orm import Session
from app.features.recommendations.schemas import ExercisePlan, NutritionTargets, PreventiveTests, RecommendationResponse
from app.features.profile.services import get_health_profile
from app.features.score.services import get_latest_health_score

def generate_recommendations(db: Session, user_id: int) -> RecommendationResponse:
    """Generates personalized diet, exercise, and testing recommendations based on health profile."""
    # 1. Fetch user data
    profile = get_health_profile(db, user_id)
    score_log = get_latest_health_score(db, user_id)
    
    # Establish defaults
    weight = 70.0
    age = 30
    exercise_freq = "rarely"
    has_diabetes = "no"
    has_hypertension = "no"
    has_cholesterol = "no"
    score = 80
    
    if profile:
        weight = profile.weight or 70.0
        exercise_freq = profile.exercise_frequency
        has_diabetes = profile.has_diabetes
        has_hypertension = profile.has_hypertension
        has_cholesterol = profile.has_cholesterol
        
    if score_log:
        score = score_log.score
        if "actual_age" in score_log.factors:
            age = score_log.factors["actual_age"]

    # 2. Build Exercise Recommendation
    routines = ["30 minutes walking daily"]
    rationale_exercise = "Based on sedentary profile. Goal is to build cardiovascular base."
    frequency = "Daily"
    
    if score > 85:
        routines = ["45 minutes strength training", "20 minutes high-intensity interval training (HIIT)"]
        rationale_exercise = "Excellent score. Recommending progressive overload and cardio routines."
        frequency = "4-5 times a week"
    elif exercise_freq == "rarely":
        routines = ["20 minutes light mobility exercises", "15 minutes brisk walking"]
        rationale_exercise = "Low exercise frequency. Goal is to build a habit with gentle routines."
        frequency = "3 times a week"

    exercise_plan = ExercisePlan(
        plan_name="Cardio & Strength Starter Plan",
        frequency=frequency,
        routines=routines,
        rationale=rationale_exercise
    )

    # 3. Build Nutrition Recommendation
    protein = weight * 1.2  # 1.2g per kg
    water = 3.0
    calories = 2000.0
    suggestions = ["Oats with berries for breakfast", "Grilled chicken/tofu salad for lunch", "Steamed vegetables and quinoa for dinner"]
    rationale_nutrition = "Balanced diet focused on moderate protein and caloric maintenance."

    if has_diabetes == "yes" or (score_log and score_log.factors.get("hba1c_level") and score_log.factors["hba1c_level"] > 6.5):
        suggestions = ["Chia seed pudding", "Leafy greens and salmon/lentil salad", "Cauliflower rice with baked chicken/paneer"]
        rationale_nutrition = "Low glycemic diet recommended to help regulate HbA1c levels."
        calories = 1800.0
        
    if has_cholesterol == "yes":
        suggestions.append("Incorporate walnuts and olive oil to increase HDL.")
        rationale_nutrition += " Added heart-healthy fats to manage LDL cholesterol levels."

    nutrition_targets = NutritionTargets(
        protein_target_g=protein,
        water_target_l=water,
        calorie_target_kcal=calories,
        meal_suggestions=suggestions,
        rationale=rationale_nutrition
    )

    # 4. Build Preventive Tests Recommendation
    tests = ["Complete Blood Count (CBC)"]
    rationale_tests = "General health monitoring."
    frequency_tests = "Annual"

    if age > 40:
        tests.append("Lipid Profile")
        tests.append("HbA1c")
        rationale_tests += " Recommended due to age factor (>40) to screen metabolic risks."

    if has_diabetes == "family_history" or has_diabetes == "yes":
        if "HbA1c" not in tests:
            tests.append("HbA1c")
        rationale_tests += " Prioritizing HbA1c screening due to diabetes indicators."
        frequency_tests = "Every 6 months"

    preventive_tests = PreventiveTests(
        recommended_tests=tests,
        frequency=frequency_tests,
        rationale=rationale_tests
    )

    return RecommendationResponse(
        exercise=exercise_plan,
        nutrition=nutrition_targets,
        preventive_tests=preventive_tests
    )
