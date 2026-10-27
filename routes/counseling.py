from flask import Blueprint, request, redirect, url_for, flash, session
from models import db, Student, Counseling, AuditLog
from routes.auth import login_required, role_required
from datetime import datetime

counseling_bp = Blueprint('counseling', __name__)

@counseling_bp.route('/counseling/schedule', methods=['POST'])
@login_required
@role_required('Admin', 'Counselor', 'Mentor')
def schedule_session():
    try:
        student_id = int(request.form.get('student_id'))
        counselor_id = int(request.form.get('counselor_id'))
        scheduled_date_str = request.form.get('scheduled_date')
        
        # Parse datetime
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
        
        student = Student.query.get_or_404(student_id)
        
        session_log = Counseling(
            student_id=student_id,
            counselor_id=counselor_id,
            scheduled_date=scheduled_date,
            status='Scheduled'
        )
        db.session.add(session_log)
        
        # Send parent notification for scheduled counseling session
        from models import ParentNotification
        pn = ParentNotification(
            student_id=student.id,
            student_name=student.name,
            parent_phone=student.phone or "9999999999",
            parent_email=student.email or "parent@academia.edu",
            notification_type="Counseling Scheduled",
            message=f"Dear Parent/Guardian, a counseling session has been scheduled for your ward {student.name} on {scheduled_date.strftime('%d-%b-%Y %I:%M %p')}. Kindly encourage them to attend.",
            status="Sent",
            channel="Email & SMS"
        )
        db.session.add(pn)
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Schedule Counseling",
            target_table="counseling",
            details=f"Scheduled counseling session for student {student.name} on {scheduled_date_str}.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"Counseling session scheduled for {student.name} successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error scheduling session: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.counseling_dashboard'))

@counseling_bp.route('/counseling/complete/<int:id>', methods=['POST'])
@login_required
@role_required('Admin', 'Counselor', 'Mentor')
def complete_session(id):
    try:
        session_log = Counseling.query.get_or_404(id)
        notes = request.form.get('notes')
        actions_taken = request.form.get('actions_taken')
        
        session_log.notes = notes
        session_log.actions_taken = actions_taken
        session_log.status = 'Completed'
        
        # Capture snapshot of student performance before intervention
        student = session_log.student
        session_log.gpa_before = student.current_gpa
        session_log.backlogs_before = student.backlogs
        session_log.assignment_before = student.assignment_rate
        session_log.risk_score_before = student.risk_score
        session_log.risk_level_before = student.risk_level
        
        # Calculate average internal marks before
        from sqlalchemy import func
        from models import Marks
        avg_marks = db.session.query(func.avg(Marks.marks_obtained)).filter_by(student_id=student.id, exam_type='Internal').scalar()
        session_log.internal_marks_before = float(avg_marks) if avg_marks is not None else 70.0
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Complete Counseling",
            target_table="counseling",
            details=f"Completed counseling session for student {session_log.student.name}. Notes: {notes[:50]}...",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash("Counseling session marked as completed with feedback notes.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error completing session: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.counseling_dashboard'))

@counseling_bp.route('/counseling/cancel/<int:id>', methods=['POST'])
@login_required
@role_required('Admin', 'Counselor', 'Mentor')
def cancel_session(id):
    try:
        session_log = Counseling.query.get_or_404(id)
        session_log.status = 'Cancelled'
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Cancel Counseling",
            target_table="counseling",
            details=f"Cancelled counseling session for student {session_log.student.name}.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash("Counseling session has been cancelled.", "warning")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling session: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('main.counseling_dashboard'))
