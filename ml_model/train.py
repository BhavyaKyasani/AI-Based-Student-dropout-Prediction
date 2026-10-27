import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import joblib
import json

def generate_synthetic_data(num_samples=1200):
    """
    Generates a realistic student dataset for dropout prediction without attendance features.
    Features:
      - current_gpa: float (4.0 to 10.0)
      - prev_gpa: float (4.0 to 10.0)
      - backlogs: int (0 to 8)
      - fee_due: float (0 to 150,000)
      - assignment_rate: float (30 to 100)
      - lab_marks: float (40 to 100)
      - semester: int (1 to 8)
      - gpa_trend: float (-2.0 to 2.0)
      - counseling_count: int (0 to 5)
    """
    np.random.seed(42)
    
    current_gpa = np.random.uniform(4.0, 9.8, num_samples)
    prev_gpa = np.random.uniform(4.0, 9.8, num_samples)
    attendance_rate = np.random.uniform(50.0, 100.0, num_samples)
    backlogs = np.random.poisson(0.5, num_samples)
    backlogs = np.clip(backlogs, 0, 8)
    
    fee_due = np.random.choice([0.0, 50000.0, 100000.0, 150000.0], size=num_samples, p=[0.5, 0.25, 0.15, 0.1])
    assignment_rate = np.random.uniform(55, 100, num_samples)
    lab_marks = np.random.uniform(50, 100, num_samples)
    semester = np.random.randint(1, 9, num_samples)
    counseling_count = np.random.poisson(0.3, num_samples)
    counseling_count = np.clip(counseling_count, 0, 5)
    
    # Calculate GPA trend
    gpa_trend = current_gpa - prev_gpa
    
    # Adjust variables to create realistic correlations
    for i in range(num_samples):
        if current_gpa[i] < 6.0:
            attendance_rate[i] -= np.random.uniform(5, 25)
            assignment_rate[i] -= np.random.uniform(5, 25)
            lab_marks[i] -= np.random.uniform(5, 20)
        if backlogs[i] > 2:
            current_gpa[i] -= np.random.uniform(0.5, 2.0)
            gpa_trend[i] -= np.random.uniform(0.2, 0.8)
        current_gpa[i] = np.clip(current_gpa[i], 2.0, 10.0)
        attendance_rate[i] = np.clip(attendance_rate[i], 30, 100)
        assignment_rate[i] = np.clip(assignment_rate[i], 20, 100)
        lab_marks[i] = np.clip(lab_marks[i], 20, 100)
        gpa_trend[i] = current_gpa[i] - prev_gpa[i]
        
    # Define risk rules to construct the target variable 'dropout' (probability-based)
    risk_score = (
        (10 - current_gpa) * 4.0 + 
        (100 - attendance_rate) * 0.35 +
        backlogs * 4.5 + 
        (fee_due / 15000) * 1.5 + 
        (100 - assignment_rate) * 0.15 +
        (100 - lab_marks) * 0.15 +
        (-gpa_trend) * 4.0 +
        (10 - prev_gpa) * 1.5
    )
    
    # Add random noise
    risk_score += np.random.normal(0, 5, num_samples)
    
    # Probability of dropout
    prob = 1 / (1 + np.exp(-(risk_score - 38) / 8))
    dropout = np.random.binomial(1, prob)
    
    df = pd.DataFrame({
        'current_gpa': current_gpa,
        'prev_gpa': prev_gpa,
        'attendance_rate': attendance_rate,
        'backlogs': backlogs,
        'fee_due': fee_due,
        'assignment_rate': assignment_rate,
        'lab_marks': lab_marks,
        'semester': semester,
        'gpa_trend': gpa_trend,
        'counseling_count': counseling_count,
        'dropout': dropout
    })
    
    return df

def main():
    print("Generating synthetic student data...")
    df = generate_synthetic_data(1500)
    
    X = df.drop('dropout', axis=1)
    y = df['dropout']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        'Logistic Regression': LogisticRegression(random_state=42),
        'Decision Tree': DecisionTreeClassifier(max_depth=5, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
        'XGBoost': xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42, eval_metric='logloss')
    }
    
    metrics_summary = {}
    best_f1 = 0
    best_model_name = ""
    best_model = None
    
    print("\nTraining and evaluating models...")
    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        y_prob = model.predict_proba(X_test_scaled)[:, 1]
            
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)
        
        metrics_summary[name] = {
            'Accuracy': float(acc),
            'Precision': float(prec),
            'Recall': float(rec),
            'F1_Score': float(f1),
            'ROC_AUC': float(auc)
        }
        
        print(f"{name}: Accuracy={acc:.4f}, Precision={prec:.4f}, Recall={rec:.4f}, F1={f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model
            
    print(f"\nBest Model: {best_model_name} with F1-Score of {best_f1:.4f}")
    
    os.makedirs('ml_model', exist_ok=True)
    joblib.dump(best_model, 'ml_model/model.pkl')
    joblib.dump(scaler, 'ml_model/scaler.pkl')
    
    # Get feature importances
    feature_names = list(X.columns)
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
    elif hasattr(best_model, 'coef_'):
        importances = np.abs(best_model.coef_[0])
        importances = importances / np.sum(importances)
    else:
        importances = np.ones(len(feature_names)) / len(feature_names)
        
    feature_importance_dict = {name: float(imp) for name, imp in zip(feature_names, importances)}
    
    metadata = {
        'best_model_name': best_model_name,
        'metrics': metrics_summary,
        'feature_importances': feature_importance_dict,
        'feature_names': feature_names
    }
    
    with open('ml_model/model_metrics.json', 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print("Saved model artifacts to ml_model/ directory.")

if __name__ == '__main__':
    main()
