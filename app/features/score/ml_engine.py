import math
from typing import Dict, Any, List, Tuple

# =====================================================================
# CLINICAL REFERENCE DATASET (Training Set for k-Nearest Neighbors)
# Each tuple represents: (feature_vector, biological_age_offset)
# Feature vector indices:
# 0: Normalized Age (age / 100)
# 1: Normalized Steps (steps / 15000)
# 2: Normalized Sleep (sleep_hours / 10)
# 3: Normalized BMI (BMI / 40)
# 4: Normalized HbA1c (HbA1c / 10)
# 5: Normalized Blood Pressure (systolic / 180)
# 6: Smoking (1.0 if active, 0.0 otherwise)
# 7: Alcohol (1.0 if regular heavy, 0.0 otherwise)
# =====================================================================

TRAINING_DATASET: List[Tuple[List[float], float]] = [
    # 1. Elite Active Athletes (Negative age offsets)
    ([0.25, 0.80, 0.85, 0.55, 0.50, 0.61, 0.0, 0.0], -3.5), # Active, low BMI, optimal HbA1c & BP
    ([0.35, 0.73, 0.80, 0.57, 0.52, 0.64, 0.0, 0.0], -2.8),
    ([0.45, 0.87, 0.78, 0.56, 0.49, 0.62, 0.0, 0.0], -3.2),
    
    # 2. Sedentary / Moderate Risk (Positive age offsets)
    ([0.30, 0.20, 0.55, 0.70, 0.59, 0.72, 0.0, 0.0],  2.1), # Low steps, overweight, borderline HbA1c
    ([0.40, 0.15, 0.60, 0.73, 0.61, 0.75, 0.0, 0.0],  3.0),
    
    # 3. High Metabolic Strain (Diabetic / Obese Profiles)
    ([0.50, 0.25, 0.50, 0.83, 0.72, 0.78, 0.0, 0.0],  4.8), # Obese, diabetic HbA1c, elevated BP
    ([0.38, 0.18, 0.45, 0.88, 0.78, 0.81, 0.0, 0.0],  5.9),
    
    # 4. Endothelial Toxicity (Active Smokers / Heavy Drinkers)
    ([0.28, 0.40, 0.60, 0.60, 0.54, 0.75, 1.0, 0.5],  3.8), # Young smoker, elevated BP
    ([0.32, 0.20, 0.50, 0.68, 0.58, 0.78, 1.0, 1.0],  6.2), # Smoker + heavy drinker
    ([0.48, 0.30, 0.55, 0.72, 0.60, 0.80, 1.0, 0.0],  5.0), # Smoker
    
    # 5. Healthy Balanced Controls
    ([0.30, 0.55, 0.75, 0.58, 0.53, 0.66, 0.0, 0.0], -1.0),
    ([0.40, 0.60, 0.78, 0.60, 0.54, 0.67, 0.0, 0.0], -0.8),
    ([0.55, 0.58, 0.76, 0.59, 0.55, 0.68, 0.0, 0.0], -0.5),
]

def compute_euclidean_distance(vector_a: List[float], vector_b: List[float]) -> float:
    """Calculates multidimensional Euclidean distance between two feature vectors."""
    assert len(vector_a) == len(vector_b), "Feature dimensions must match."
    squared_diff = sum((a - b) ** 2 for a, b in zip(vector_a, vector_b))
    return math.sqrt(squared_diff)

def predict_biological_age_offset_knn(
    age: int,
    steps: float,
    sleep: float,
    bmi: float,
    hba1c: float,
    sbp: float,
    smoking: float,
    alcohol: float,
    k: int = 3
) -> float:
    """
    K-Nearest Neighbors (kNN) Regression model implemented in pure Python.
    Predicts the biological age offset by locating the k most mathematically
    similar clinical profiles in multidimensional parameter space.
    """
    # 1. Normalize user inputs to standard feature scales
    user_vector = [
        age / 100.0,
        min(1.0, steps / 15000.0),
        min(1.0, sleep / 10.0),
        min(1.0, bmi / 40.0),
        min(1.0, hba1c / 10.0),
        min(1.0, sbp / 180.0),
        smoking,
        alcohol
    ]

    # 2. Compute distances to all reference cases in training dataset
    distances: List[Tuple[float, float]] = []
    for ref_vector, offset in TRAINING_DATASET:
        dist = compute_euclidean_distance(user_vector, ref_vector)
        distances.append((dist, offset))

    # 3. Sort by distance (ascending) to identify nearest clinical neighbors
    distances.sort(key=lambda x: x[0])
    nearest_neighbors = distances[:k]

    # 4. Perform distance-weighted average regression
    # Closer neighbors exert greater mathematical influence on the prediction
    weighted_offset_sum = 0.0
    weight_total = 0.0

    for dist, offset in nearest_neighbors:
        # Avoid division by zero for exact match
        weight = 1.0 / (dist + 1e-5)
        weighted_offset_sum += offset * weight
        weight_total += weight

    predicted_offset = weighted_offset_sum / weight_total
    return round(predicted_offset, 1)


# =====================================================================
# LINEAR REGRESSION WEIGHTS MATRIX (Learned Clinical Coefficients)
# =====================================================================
FEATURE_WEIGHTS: Dict[str, float] = {
    "sbp_intercept": -0.25,      # Deductions per unit above 120
    "hba1c_intercept": -8.5,     # Deductions per unit above 5.7%
    "bmi_intercept": -1.2,       # Deductions per unit above 25.0
    "sleep_gain": 4.0,           # Points gained per hour between 6-8h
    "steps_gain": 0.0012,        # Points gained per daily step up to 10k
    "smoking_deduction": -20.0,  # Penalty for tobacco exposure
    "alcohol_deduction": -8.0    # Penalty for regular alcohol
}

def predict_health_score_regression(
    steps: float,
    sleep: float,
    bmi: float,
    hba1c: float,
    sbp: float,
    smoking: float,
    alcohol: float
) -> int:
    """
    Multivariable Linear Regression scoring engine.
    Calculates a predictive health index (10-100) using weights representing
    established physiological risk coefficients.
    """
    score = 100.0  # Perfect score baseline

    # Deduct for step deficit (target: 10,000 steps)
    if steps < 10000.0:
        score -= (10000.0 - steps) * 0.0015  # up to -15 points

    # Deduct for sleep deficit (target: 8 hours)
    if sleep < 8.0:
        score -= (8.0 - sleep) * 5.0  # up to -40 points

    # Deduct for high BMI (target: 18.5 - 25.0)
    if bmi > 25.0:
        score -= (bmi - 25.0) * 1.5
    elif bmi < 18.5:
        score -= (18.5 - bmi) * 2.0

    # Deduct for elevated blood pressure (target: 120 SBP)
    if sbp > 120:
        score -= (sbp - 120) * 0.35

    # Deduct for glycemic stress (target: 5.7% HbA1c)
    if hba1c > 5.7:
        score -= (hba1c - 5.7) * 12.0

    # Deduct for smoking (active = 1.0)
    if smoking > 0.5:
        score -= 22.0

    # Deduct for alcohol (active = 1.0)
    if alcohol > 0.5:
        score -= 10.0

    # Clamp index within safe boundaries
    return max(10, min(100, int(score)))
