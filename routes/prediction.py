from flask import Blueprint, request, redirect, url_for, flash, session, g
from models import db, Student, Prediction, Alert, AuditLog
from routes.auth import login_required, role_required
from datetime import datetime
import json

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/prediction/run-all', methods=['POST'])
@login_required
@role_required('Admin', 'Principal', 'Faculty')
def run_all_predictions():
    try:
        students = Student.query.all()
        if not students:
            flash("No students found to predict.", "warning")
            return redirect(url_for('main.dashboard'))
            
        from ml_model.predict import predict_student_risk
        
        predictions_run = 0
        high_risk_count = 0
        
        for student in students:
            # Count completed counseling sessions dynamically
            from models import Counseling
            counseling_count = Counseling.query.filter_by(student_id=student.id, status='Completed').count()
            
            features = {
                'current_gpa': student.current_gpa,
                'prev_gpa': student.prev_gpa,
                'attendance_rate': student.attendance_rate,
                'backlogs': student.backlogs,
                'fee_due': student.fee_due,
                'assignment_rate': student.assignment_rate,
                'lab_marks': student.lab_marks,
                'semester': student.semester,
                'gpa_trend': student.current_gpa - student.prev_gpa,
                'counseling_count': counseling_count
            }
            
            # Predict
            pred_res = predict_student_risk(features)
            
            # Update student record
            student.risk_score = pred_res['risk_score']
            student.risk_level = pred_res['risk_level']
            student.predicted_at = datetime.utcnow()
            student.reasons = ", ".join(pred_res['reasons'])
            
            # Save prediction history
            model_name = 'XGBoost'
            import os
            metrics_path = 'ml_model/model_metrics.json'
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, 'r') as f:
                        model_name = json.load(f).get('best_model_name', 'XGBoost')
                except:
                    pass

            prediction_log = Prediction(
                student_id=student.id,
                risk_score=pred_res['risk_score'],
                risk_level=pred_res['risk_level'],
                model_used=model_name,
                feature_importance_json=json.dumps(pred_res['reasons']),
                reasons_json=json.dumps(pred_res['reasons'])
            )
            db.session.add(prediction_log)
            
            # Raise alert if Medium or High risk
            if pred_res['risk_level'] in ['Medium', 'High']:
                high_risk_count += 1
                # Check if there is already an active alert to prevent duplicate spam
                existing_alert = Alert.query.filter_by(
                    student_id=student.id, 
                    risk_level=pred_res['risk_level'],
                    status='Pending'
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        student_id=student.id,
                        message=f"System generated: Student {student.name} is classified as {pred_res['risk_level']} Risk. Reasons: {student.reasons}",
                        risk_level=pred_res['risk_level'],
                        status='Pending',
                        notification_type='Email'
                    )
                    db.session.add(alert)
                    
            predictions_run += 1
            
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Run Batch Prediction",
            target_table="predictions",
            details=f"Ran batch prediction engine for {predictions_run} students. Detected {high_risk_count} medium/high risk students.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"AI Batch Prediction complete! Calculated risk for {predictions_run} students.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error running predictions: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.dashboard'))

@prediction_bp.route('/prediction/retrain', methods=['POST'])
@login_required
@role_required('Admin')
def retrain_model():
    try:
        from ml_model.train import main as train_model
        
        # Call training function
        train_model()
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Retrain ML Model",
            details="Successfully retrained model with updated dataset.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash("Machine Learning Model retrained successfully and updated dashboard metrics.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error retraining model: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.admin_dashboard'))
