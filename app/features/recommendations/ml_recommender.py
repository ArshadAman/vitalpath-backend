import math
from typing import List, Dict, Any, Tuple

# =====================================================================
# COSINE SIMILARITY RECOMMENDATION ENGINE (Vector Space Model)
# User Vector format (10 dimensions):
# 0: calorie_target_direction (-1.0 weight_loss, 1.0 muscle_gain, 0.0 wellness)
# 1: protein_density (0.0 low, 0.5 moderate, 1.0 high/muscle)
# 2: sodium_restriction (1.0 if BP elevated >= 130, 0.0 otherwise)
# 3: glycemic_control (1.0 if HbA1c >= 5.7 or Glucose >= 100, 0.0 otherwise)
# 4: cardio_focus (1.0 if goal is weight_loss / longevity, 0.0 otherwise)
# 5: hypertrophy_focus (1.0 if goal is muscle_gain, 0.0 otherwise)
# 6: mobility_focus (1.0 if sedentary or longevity-focused, 0.0 otherwise)
# 7: diet_vegetarian (1.0 if vegetarian, 0.0 otherwise)
# 8: diet_vegan (1.0 if vegan, 0.0 otherwise)
# 9: fiber_density (1.0 if total cholesterol >= 200, 0.0 otherwise)
# =====================================================================

# 1. Exercise Template Corpus (with pre-defined attribute vectors)
EXERCISE_CORPUS = [
    {
        "id": "weight_loss_cardio",
        "plan_name": "Caloric Depletion & Fat Burn Plan",
        "frequency": "5 times a week",
        "routines": [
            "35 minutes high-intensity interval training (HIIT) to optimize metabolic rate",
            "45 minutes fasted steady-state zone-2 cardio (brisk walk/cycle)",
            "15 minutes core stability and flexibility workout"
        ],
        "rationale": "Focusing on zone-2 aerobic fat oxidation and post-exercise oxygen consumption (EPOC).",
        # Vectors corresponding to the 10 dimensions:
        "vector": [-0.8, 0.4, 0.0, 0.0, 1.0, 0.0, 0.2, 0.0, 0.0, 0.0]
    },
    {
        "id": "hypertrophy_resistance",
        "plan_name": "Hypertrophy & Resistance Protocol",
        "frequency": "4 times a week",
        "routines": [
            "Warm-up: 5 minutes mobility movements",
            "45 minutes heavy resistance training (squats, bench press, deadlifts, pull-ups)",
            "Target progressive overload: increase weights weekly by 2-5%",
            "Cool-down: 10 minutes static stretching"
        ],
        "rationale": "Designed to trigger myofibrillar protein synthesis and muscle hypertrophy.",
        "vector": [0.8, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    },
    {
        "id": "longevity_endothelial",
        "plan_name": "Longevity & Endothelial Base Plan",
        "frequency": "Daily",
        "routines": [
            "40 minutes brisk walking or zone-2 jogging to maintain vascular nitric oxide release",
            "20 minutes functional strength exercises (bodyweight squats, planks, push-ups)",
            "15 minutes stretching and balance training (yoga/tai-chi)"
        ],
        "rationale": "Focusing on preserving arterial elasticity, VO2 max base, and joint stability.",
        "vector": [0.0, 0.3, 0.4, 0.0, 0.8, 0.0, 1.0, 0.0, 0.0, 0.0]
    },
    {
        "id": "habit_restorer",
        "plan_name": "Active Habit Restorer Starter",
        "frequency": "3 times a week",
        "routines": [
            "20 minutes light joints mobility exercises",
            "20 minutes moderate brisk walking",
            "Deep diaphragmatic breathing session (5 mins)"
        ],
        "rationale": "Low current activity base. Focus is on gradual habit integration without joint strain.",
        "vector": [0.0, 0.2, 0.0, 0.0, 0.2, 0.0, 0.8, 0.0, 0.0, 0.0]
    }
]

# 2. Nutrition Template Corpus
NUTRITION_CORPUS = [
    {
        "id": "veg_diabetic_low_carb",
        "plan_name": "Vegetarian Low-Glycemic Protocol",
        "meal_suggestions": [
            "Breakfast: Chia seed pudding with almond milk and crushed walnuts",
            "Lunch: Grilled tofu burger patty with low-carb green salad and olive dressing",
            "Dinner: Cauliflower rice bowl with baked paneer cubes and broccoli florets"
        ],
        "protein_factor": 1.4,
        "calorie_adjustment": -300.0,
        "rationale": "Low glycemic vegetarian load to stabilize blood insulin and prevent HbA1c spikes.",
        "vector": [-0.5, 0.6, 0.2, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.5]
    },
    {
        "id": "vegan_keto_clean",
        "plan_name": "Vegan Clean Keto & Fiber Plan",
        "meal_suggestions": [
            "Breakfast: Avocado coconut shake with hemp seeds and raw pumpkin seeds",
            "Lunch: Tempeh salad bowl with extra virgin olive oil and green leafy microgreens",
            "Dinner: Shaved broccoli steak and baked tofu stir-fry with almonds"
        ],
        "protein_factor": 1.5,
        "calorie_adjustment": -200.0,
        "rationale": "Vegan ketogenic profile with high soluble fiber density to promote blood lipid clearance.",
        "vector": [-0.3, 0.7, 0.1, 0.6, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
    },
    {
        "id": "nonveg_balanced_hypertrophy",
        "plan_name": "Clean Hypertrophy Nutrition Protocol",
        "meal_suggestions": [
            "Breakfast: Egg white scramble with spinach, mushrooms, and half an avocado",
            "Lunch: Grilled wild-caught salmon or chicken breast with quinoa and steamed broccoli",
            "Dinner: Baked cod or lean turkey steak with asparagus and roasted sweet potato"
        ],
        "protein_factor": 2.0,
        "calorie_adjustment": 300.0,
        "rationale": "Hypercaloric high-protein profile to fuel hypertrophy and recovery.",
        "vector": [0.8, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    },
    {
        "id": "veg_balanced_maintenance",
        "plan_name": "Vegetarian Cardio & Wellness Diet",
        "meal_suggestions": [
            "Breakfast: Oats with chia seeds, raw almond butter, and blue berries",
            "Lunch: Double lentil soup (dal) with brown rice and a side of cucumber salad",
            "Dinner: Paneer cubes cooked in spinach paste (Palak Paneer) with 2 multi-grain rotis"
        ],
        "protein_factor": 1.2,
        "calorie_adjustment": 0.0,
        "rationale": "Eucaloric vegetarian nutrition plan supporting cardioprotective metrics.",
        "vector": [0.0, 0.4, 0.0, 0.0, 0.5, 0.0, 0.5, 1.0, 0.0, 0.2]
    }
]

# 3. Preventive Tests Corpus
PREVENTIVE_CORPUS = [
    {
        "id": "cardio_metabolic_panel",
        "recommended_tests": ["Complete Blood Count (CBC)", "Lipid Profile Panel", "HbA1c"],
        "frequency": "Every 6 months",
        "rationale": "Indicated due to cardiovascular SBP metrics, cholesterol values, or elevated glycemic readings.",
        "vector": [0.0, 0.0, 0.8, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8]
    },
    {
        "id": "deficiency_recheck_panel",
        "recommended_tests": ["Complete Blood Count (CBC)", "25-OH Vitamin D3", "Iron Studies & Ferritin"],
        "frequency": "Every 3 months",
        "rationale": "Vitamin D3 or iron/hemoglobin indicators fell below optimal clinical ranges during screening.",
        "vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0]
    },
    {
        "id": "annual_surveillance",
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "frequency": "Annual",
        "rationale": "General health surveillance checks for active low-risk demographics.",
        "vector": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
]

def calculate_cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Computes the cosine of the angle between two vectors in multi-dimensional space."""
    assert len(vector_a) == len(vector_b), "Vector dimensions must be equal"
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a ** 2 for a in vector_a))
    norm_b = math.sqrt(sum(b ** 2 for b in vector_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def build_user_vector(
    goal: str,
    diet: str,
    weight: float,
    sbp: float,
    hba1c: float,
    cholesterol: float,
    steps: float,
    sleep: float,
    vit_d3: float,
    hemoglobin: float
) -> List[float]:
    """Constructs a normalized 10-dimensional physiology state vector for similarity calculations."""
    # 0: calorie_target_direction
    cal_dir = 0.0
    if goal == "weight_loss":
        cal_dir = -0.8
    elif goal == "muscle_gain":
        cal_dir = 0.8
        
    # 1: protein_density
    prot = 0.4
    if goal == "muscle_gain":
        prot = 1.0
    elif goal == "weight_loss":
        prot = 0.8

    # 2: sodium_restriction
    sodium = 1.0 if sbp >= 130 else (0.5 if sbp >= 125 else 0.0)

    # 3: glycemic_control
    glycemic = 1.0 if hba1c >= 5.7 else 0.0

    # 4: cardio_focus
    cardio = 1.0 if goal in ["weight_loss", "longevity"] else 0.2

    # 5: hypertrophy_focus
    hypertrophy = 1.0 if goal == "muscle_gain" else 0.0

    # 6: mobility_focus
    mobility = 1.0 if (steps < 5000 or goal == "longevity") else 0.2

    # 7: diet_vegetarian
    vegetarian = 1.0 if diet == "vegetarian" else 0.0

    # 8: diet_vegan
    vegan = 1.0 if diet == "vegan" else 0.0

    # 9: fiber_density
    fiber = 1.0 if cholesterol >= 200 else 0.0

    return [
        cal_dir,
        prot,
        sodium,
        glycemic,
        cardio,
        hypertrophy,
        mobility,
        vegetarian,
        vegan,
        fiber
    ]

def get_best_match_recommendations(
    goal: str,
    diet: str,
    weight: float,
    sbp: float,
    hba1c: float,
    cholesterol: float,
    steps: float,
    sleep: float,
    vit_d3: float,
    hemoglobin: float
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Computes Cosine Similarity between user state and template vector spaces.
    Selects the most suitable exercise, diet, and clinical plans dynamically.
    """
    user_vector = build_user_vector(
        goal, diet, weight, sbp, hba1c, cholesterol, steps, sleep, vit_d3, hemoglobin
    )

    # 1. Match Exercise
    best_exercise = max(
        EXERCISE_CORPUS,
        key=lambda x: calculate_cosine_similarity(user_vector, x["vector"])
    )

    # 2. Match Nutrition (with pre-filtering for dietary constraints)
    eligible_nutrition = NUTRITION_CORPUS
    if diet == "vegan":
        eligible_nutrition = [n for n in NUTRITION_CORPUS if n["vector"][8] == 1.0]
    elif diet == "vegetarian":
        eligible_nutrition = [n for n in NUTRITION_CORPUS if n["vector"][7] == 1.0 or n["vector"][8] == 1.0]

    if not eligible_nutrition:
        eligible_nutrition = NUTRITION_CORPUS

    best_nutrition = max(
        eligible_nutrition,
        key=lambda x: calculate_cosine_similarity(user_vector, x["vector"])
    )

    # 3. Match Preventive Tests
    best_preventive = max(
        PREVENTIVE_CORPUS,
        key=lambda x: calculate_cosine_similarity(user_vector, x["vector"])
    )

    # For clinical deficiencies, dynamically append targeted tests to best matched tests
    matched_tests = list(best_preventive["recommended_tests"])
    matched_rationale = best_preventive["rationale"]
    matched_frequency = best_preventive["frequency"]

    if vit_d3 < 30 and "25-OH Vitamin D3" not in matched_tests:
        matched_tests.append("25-OH Vitamin D3")
        matched_rationale += " Appended Vitamin D3 deficiency surveillance check."
        matched_frequency = "Every 3 months"

    if hemoglobin < 12.0 and "Iron Studies & Ferritin" not in matched_tests:
        matched_tests.append("Iron Studies & Ferritin")
        matched_rationale += " Appended diagnostic iron profiles due to low hemoglobin."
        matched_frequency = "Every 3 months"

    adjusted_preventive = {
        "recommended_tests": matched_tests,
        "frequency": matched_frequency,
        "rationale": matched_rationale
    }

    return best_exercise, best_nutrition, adjusted_preventive
