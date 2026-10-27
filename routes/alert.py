from flask import Blueprint, request, redirect, url_for, flash, session
from models import db, Alert, AuditLog
from routes.auth import login_required, role_required
from datetime import datetime

alert_bp = Blueprint('alert', __name__)

@alert_bp.route('/alert/send/<int:id>', methods=['POST'])
@login_required
def send_notification(id):
    try:
        alert = Alert.query.get_or_404(id)
        notification_type = request.form.get('notification_type', 'Email')
        
        # Simulate dispatching communications
        alert.status = 'Sent'
        alert.sent_at = datetime.utcnow()
        alert.notification_type = notification_type
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Send Alert Notification",
            target_table="alerts",
            details=f"Dispatched {notification_type} alert for student {alert.student.name} ({alert.risk_level} Risk).",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"Notification successfully sent via {notification_type} to mentor and guardian.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error sending notification: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.notification_dashboard'))

@alert_bp.route('/alert/dismiss/<int:id>', methods=['POST'])
@login_required
@role_required('Admin', 'Counselor', 'Mentor')
def dismiss_alert(id):
    try:
        alert = Alert.query.get_or_404(id)
        db.session.delete(alert)
        
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Dismiss Alert",
            target_table="alerts",
            details=f"Dismissed alert for student {alert.student.name}.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash("Alert dismissed and removed from dashboard logs.", "info")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error dismissing alert: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.notification_dashboard'))
