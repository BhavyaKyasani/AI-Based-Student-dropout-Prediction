from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Mentor') # Admin, Mentor, Counselor, Faculty, Principal
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    counselings = db.relationship('Counseling', backref='counselor', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False) # e.g. CSE, ECE, MECH
    
    # Relationships
    students = db.relationship('Student', backref='department', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'student_count': len(self.students)
        }

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False) # College roll number / ID
    password_hash = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False) # Male, Female, Other
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False, default=1)
    
    # Dynamic values (updated by system / prediction run)
    current_gpa = db.Column(db.Float, default=0.0)
    prev_gpa = db.Column(db.Float, default=0.0)
    attendance_rate = db.Column(db.Float, default=95.0) # Attendance %
    backlogs = db.Column(db.Integer, default=0)
    fee_due = db.Column(db.Float, default=0.0)
    assignment_rate = db.Column(db.Float, default=100.0) # Homework completion %
    lab_marks = db.Column(db.Float, default=100.0) # Average lab score %
    
    # Risk Engine outcomes
    risk_score = db.Column(db.Float, default=0.0) # 0 to 100
    risk_level = db.Column(db.String(20), default='Low') # Low, Medium, High
    predicted_at = db.Column(db.DateTime, nullable=True)
    reasons = db.Column(db.Text, nullable=True) # Text description of main risk drivers
    
    # Relationships
    marks = db.relationship('Marks', backref='student', lazy=True, cascade="all, delete-orphan")
    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan")
    daily_attendances = db.relationship('DailyAttendance', backref='student', lazy=True, cascade="all, delete-orphan")
    fees = db.relationship('Fees', backref='student', lazy=True, cascade="all, delete-orphan")
    predictions = db.relationship('Prediction', backref='student', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('Alert', backref='student', lazy=True, cascade="all, delete-orphan")
    counselings = db.relationship('Counseling', backref='student', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'gender': self.gender,
            'department_code': self.department.code if self.department else 'N/A',
            'department_id': self.department_id,
            'semester': self.semester,
            'current_gpa': self.current_gpa,
            'prev_gpa': self.prev_gpa,
            'attendance_rate': self.attendance_rate,
            'backlogs': self.backlogs,
            'fee_due': self.fee_due,
            'assignment_rate': self.assignment_rate,
            'lab_marks': self.lab_marks,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'predicted_at': self.predicted_at.strftime('%Y-%m-%d %H:%M:%S') if self.predicted_at else None,
            'reasons': self.reasons
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    total_classes = db.Column(db.Integer, nullable=False, default=50)
    attended_classes = db.Column(db.Integer, nullable=False, default=45)
    percentage = db.Column(db.Float, nullable=False, default=90.0)

class DailyAttendance(db.Model):
    __tablename__ = 'daily_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Present') # Present, Absent
    marked_by = db.Column(db.String(100), nullable=True)



class Marks(db.Model):
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    exam_type = db.Column(db.String(50), nullable=False, default='Internal') # Internal, Semester

class Fees(db.Model):
    __tablename__ = 'fees'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    total_fee = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, nullable=False, default=0.0)
    due_amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid') # Paid, Partial, Unpaid
    due_date = db.Column(db.DateTime, nullable=True)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False) # Low, Medium, High
    model_used = db.Column(db.String(50), nullable=False, default='XGBoost')
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    feature_importance_json = db.Column(db.Text, nullable=True) # JSON dump of SHAP values / feature weight
    reasons_json = db.Column(db.Text, nullable=True) # JSON array of formatted reason strings

    def get_features(self):
        return json.loads(self.feature_importance_json) if self.feature_importance_json else {}
        
    def get_reasons(self):
        return json.loads(self.reasons_json) if self.reasons_json else []

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False) # Low, Medium, High
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Sent, Failed
    notification_type = db.Column(db.String(20), nullable=False, default='Email') # Email, SMS, WhatsApp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)

class Counseling(db.Model):
    __tablename__ = 'counseling'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Scheduled') # Scheduled, Completed, Cancelled
    notes = db.Column(db.Text, nullable=True)
    actions_taken = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Snapshot of metrics before counseling
    gpa_before = db.Column(db.Float, nullable=True)
    attendance_before = db.Column(db.Float, nullable=True)
    backlogs_before = db.Column(db.Integer, nullable=True)
    assignment_before = db.Column(db.Float, nullable=True)
    risk_score_before = db.Column(db.Float, nullable=True)
    risk_level_before = db.Column(db.String(20), nullable=True)
    internal_marks_before = db.Column(db.Float, nullable=True)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for system tasks / failed logins
    action = db.Column(db.String(100), nullable=False) # e.g. "Run Prediction Pipeline", "Add Student"
    target_table = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ParentNotification(db.Model):
    __tablename__ = 'parent_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    parent_email = db.Column(db.String(100), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, default='Risk Alert') # Risk Alert, Counseling, Performance Change
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Sent') # Sent, Pending, Failed
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(20), default='Email & SMS') # Email, SMS, WhatsApp

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Completed, Pending, Late
    marks_obtained = db.Column(db.Float, nullable=True)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False) # Mentor
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

def process_student_risk_updates(student, pred_res, old_risk_level=None, old_gpa=None):
    from models import db, Prediction, Alert, ParentNotification
    
    # Update student fields
    student.risk_score = pred_res['risk_score']
    student.risk_level = pred_res['risk_level']
    student.predicted_at = datetime.utcnow()
    student.reasons = ", ".join(pred_res['reasons'])
    
    # Save Prediction History Log
    prediction_log = Prediction(
        student_id=student.id,
        risk_score=pred_res['risk_score'],
        risk_level=pred_res['risk_level'],
        model_used='XGBoost',
        feature_importance_json=json.dumps(pred_res['reasons']),
        reasons_json=json.dumps(pred_res['reasons'])
    )
    db.session.add(prediction_log)
    
    # 1. Alert parents if Medium or High risk
    # Prevent duplicate spam by checking if risk level has changed
    if student.risk_level in ['Medium', 'High'] and old_risk_level != student.risk_level:
        msg = f"Dear Parent/Guardian, your ward {student.name} (ID: {student.student_id}) has been identified as having a {student.risk_level} Dropout Risk level. Major reasons: {student.reasons}. Academic counseling is recommended."
        pn = ParentNotification(
            student_id=student.id,
            student_name=student.name,
            parent_phone=student.phone or "9999999999",
            parent_email=student.email or "parent@academia.edu",
            notification_type="Risk Warning",
            message=msg,
            status="Sent"
        )
        db.session.add(pn)
        
        # Also create mentor alert
        alert = Alert(
            student_id=student.id,
            message=f"System Alert: Student {student.name} is at {student.risk_level} Risk. Reasons: {student.reasons}",
            risk_level=student.risk_level,
            status='Pending',
            notification_type='Email'
        )
        db.session.add(alert)
        
    # 2. Check for Academic Performance Improvement or Decline
    if old_gpa is not None:
        gpa_diff = student.current_gpa - old_gpa
        if gpa_diff >= 0.5:
            # Significant improvement
            msg = f"Dear Parent/Guardian, we are pleased to inform you that your ward {student.name}'s academic performance has significantly improved. Their GPA increased by {gpa_diff:.2f} points (now {student.current_gpa:.2f}). Keep up the great work!"
            pn = ParentNotification(
                student_id=student.id,
                student_name=student.name,
                parent_phone=student.phone or "9999999999",
                parent_email=student.email or "parent@academia.edu",
                notification_type="Performance Improvement",
                message=msg,
                status="Sent"
            )
            db.session.add(pn)
        elif gpa_diff <= -0.5:
            # Significant decline
            msg = f"Dear Parent/Guardian, this is to notify you that your ward {student.name}'s academic performance has significantly declined. Their GPA dropped by {abs(gpa_diff):.2f} points (now {student.current_gpa:.2f}). We recommend immediate attention and mentoring."
            pn = ParentNotification(
                student_id=student.id,
                student_name=student.name,
                parent_phone=student.phone or "9999999999",
                parent_email=student.email or "parent@academia.edu",
                notification_type="Performance Decline",
                message=msg,
                status="Sent"
            )
            db.session.add(pn)
