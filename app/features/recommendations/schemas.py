from pydantic import BaseModel
from typing import List, Dict, Any

class ExercisePlan(BaseModel):
    plan_name: str
    frequency: str
    routines: List[str]
    rationale: str

class NutritionTargets(BaseModel):
    protein_target_g: float
    water_target_l: float
    calorie_target_kcal: float
    meal_suggestions: List[str]
    rationale: str

class PreventiveTests(BaseModel):
    recommended_tests: List[str]
    frequency: str
    rationale: str

class RecommendationResponse(BaseModel):
    exercise: ExercisePlan
    nutrition: NutritionTargets
    preventive_tests: PreventiveTests
