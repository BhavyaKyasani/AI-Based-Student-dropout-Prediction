import os
import joblib
import pandas as pd
import numpy as np

# Global variables for caching model and scaler
_model = None
_scaler = None

def load_prediction_model():
    """Loads the model and scaler from disk."""
    global _model, _scaler
    if _model is None or _scaler is None:
        model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
        scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            _model = joblib.load(model_path)
            _scaler = joblib.load(scaler_path)
        else:
            raise FileNotFoundError("Model files not found. Please run train.py first to train the model.")
    return _model, _scaler

def predict_student_risk(features):
    """
    Predicts the dropout risk score and risk level for a student based on academic parameters.
    
    Parameters:
      features: dict containing:
        - current_gpa: float (0-10)
        - prev_gpa: float (0-10)
        - backlogs: int
        - fee_due: float
        - assignment_rate: float (0-100)
        - lab_marks: float (0-100)
        - semester: int (1-8)
        - gpa_trend: float
        - counseling_count: int
        
    Returns:
      dict with:
        - risk_score: float (0 to 100)
        - risk_level: str ('Low', 'Medium', 'High')
        - reasons: list of str (top risk factors)
    """
    model, scaler = load_prediction_model()
    
    feature_cols = [
        'current_gpa', 'prev_gpa', 'attendance_rate', 'backlogs', 'fee_due',
        'assignment_rate', 'lab_marks', 'semester', 'gpa_trend', 'counseling_count'
    ]
    
    input_data = pd.DataFrame([features])[feature_cols]
    
    # Scale inputs
    input_scaled = scaler.transform(input_data)
    
    # Predict probabilities (probability of dropout)
    prob = model.predict_proba(input_scaled)[0][1]
    
    # Scale probability to 0-100 risk score
    risk_score = round(float(prob * 100), 2)
    
    # Classify risk level
    if risk_score < 30:
        risk_level = 'Low'
    elif risk_score < 70:
        risk_level = 'Medium'
    else:
        risk_level = 'High'
        
    # Analyze risk factors (Explainable AI fallback)
    reasons = []
    
    if features.get('attendance_rate', 100) < 75:
        reasons.append(f"Attendance: Low class attendance rate of {features.get('attendance_rate', 0):.1f}% (below 75% requirement).")
        
    if features['current_gpa'] < 6.0:
        reasons.append(f"Academic: Low CGPA of {features['current_gpa']:.2f} (below 6.0 standard).")
        
    if features['backlogs'] > 1:
        reasons.append(f"Academic: Student has {features['backlogs']} active backlogs.")
    elif features['backlogs'] == 1:
        reasons.append("Academic: Student has 1 active backlog.")
        
    if features['gpa_trend'] < -0.3:
        reasons.append(f"Academic: Declining grade trend (GPA dropped by {abs(features['gpa_trend']):.2f} recently).")
        
    if features['assignment_rate'] < 70:
        reasons.append(f"Behavioral: Low assignment submission rate of {features['assignment_rate']:.1f}%.")
        
    if features['fee_due'] >= 50000:
        reasons.append(f"Financial: High unpaid fees (Rs. {features['fee_due']:,}).")
        
    if features['lab_marks'] < 60:
        reasons.append(f"Academic: Poor performance in internal assessments ({features['lab_marks']:.1f}%).")
        
    if features['counseling_count'] >= 2:
        reasons.append(f"Intervention: Student required {features['counseling_count']} counseling sessions due to ongoing issues.")
        
    if not reasons:
        if risk_score >= 30:
            reasons.append("General: Cumulative minor declines in grades and participation.")
        else:
            reasons.append("None: Student demonstrates healthy academic performance.")
            
    reasons = reasons[:3]
    
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'reasons': reasons
    }
