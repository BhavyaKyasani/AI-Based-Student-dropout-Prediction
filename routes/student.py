from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, g
from models import db, Student, Department, Marks, Fees, Prediction, Counseling, AuditLog
from routes.auth import login_required, role_required
from datetime import datetime
import json

student_bp = Blueprint('student', __name__)

@student_bp.route('/students', methods=['GET'])
@login_required
def list_students():
    query = Student.query
    
    # Apply Filters
    dept_id = request.args.get('department_id')
    semester = request.args.get('semester')
    risk_level = request.args.get('risk_level')
    search = request.args.get('search')
    
    if dept_id:
        query = query.filter_by(department_id=int(dept_id))
    if semester:
        query = query.filter_by(semester=int(semester))
    if risk_level:
        query = query.filter_by(risk_level=risk_level)
    if search:
        query = query.filter(Student.name.like(f"%{search}%") | Student.student_id.like(f"%{search}%"))
        
    students = query.order_by(Student.student_id).all()
    departments = Department.query.all()
    
    return render_template('students.html', 
                           students=students, 
                           departments=departments,
                           dept_id=dept_id,
                           semester=semester,
                           risk_level=risk_level,
                           search=search)

@student_bp.route('/students/add', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def add_student():
    try:
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        department_id = int(request.form.get('department_id'))
        semester = int(request.form.get('semester'))
        
        # Performance fields
        current_gpa = float(request.form.get('current_gpa', 0.0))
        prev_gpa = float(request.form.get('prev_gpa', 0.0))
        attendance_rate = float(request.form.get('attendance_rate', 95.0))
        backlogs = int(request.form.get('backlogs', 0))
        fee_due = float(request.form.get('fee_due', 0.0))
        assignment_rate = float(request.form.get('assignment_rate', 100.0))
        lab_marks = float(request.form.get('lab_marks', 100.0))
        
        # Check duplicate Student ID
        if Student.query.filter_by(student_id=student_id).first():
            flash("Roll ID already exists.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Check duplicate email
        if email and Student.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate GPA
        if not (0.0 <= current_gpa <= 10.0):
            flash("GPA must be between 0-10.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Previous GPA
        if not (0.0 <= prev_gpa <= 10.0):
            flash("Previous GPA must be between 0-10.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Assignment Rate
        if not (0.0 <= assignment_rate <= 100.0):
            flash("Assignment rate must be between 0-100.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Lab Score
        if not (0.0 <= lab_marks <= 100.0):
            flash("Lab score must be between 0-100.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Phone
        if phone:
            clean_phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
            if not clean_phone.isdigit() or len(clean_phone) < 8:
                flash("Phone number invalid.", "danger")
                return redirect(url_for('student.list_students'))
            
        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            gender=gender,
            department_id=department_id,
            semester=semester,
            current_gpa=current_gpa,
            prev_gpa=prev_gpa,
            attendance_rate=attendance_rate,
            backlogs=backlogs,
            fee_due=fee_due,
            assignment_rate=assignment_rate,
            lab_marks=lab_marks
        )
        db.session.add(student)
        db.session.flush() # Populate student.id
        
        # Set up default fee record
        fee = Fees(
            student_id=student.id,
            total_fee=150000.0,
            paid_amount=150000.0 - fee_due,
            due_amount=fee_due,
            payment_status='Paid' if fee_due == 0 else ('Unpaid' if fee_due >= 150000.0 else 'Partial'),
            due_date=datetime.utcnow()
        )
        db.session.add(fee)
        
        # Run prediction immediately on creation
        from ml_model.predict import predict_student_risk
        from models import process_student_risk_updates
        features = {
            'current_gpa': current_gpa,
            'prev_gpa': prev_gpa,
            'attendance_rate': attendance_rate,
            'backlogs': backlogs,
            'fee_due': fee_due,
            'assignment_rate': assignment_rate,
            'lab_marks': lab_marks,
            'semester': semester,
            'gpa_trend': current_gpa - prev_gpa,
            'counseling_count': 0
        }
        
        pred_res = predict_student_risk(features)
        process_student_risk_updates(student, pred_res)
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Add Student",
            target_table="students",
            details=f"Added student {name} ({student_id}) with {pred_res['risk_level']} risk.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"Student {name} added successfully! Prediction run complete: {pred_res['risk_level']} Risk.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding student: {str(e)}", "danger")
        
    return redirect(url_for('student.list_students'))


@student_bp.route('/api/students/add', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def add_student_api():
    """JSON endpoint for AJAX-based student registration from the modal form."""
    try:
        student_id      = request.form.get('student_id', '').strip()
        name            = request.form.get('name', '').strip()
        email           = request.form.get('email', '').strip()
        phone           = request.form.get('phone', '').strip()
        gender          = request.form.get('gender', 'Male')
        department_id   = int(request.form.get('department_id', 0))
        semester        = int(request.form.get('semester', 1))

        current_gpa     = float(request.form.get('current_gpa', 0.0))
        prev_gpa        = float(request.form.get('prev_gpa', 0.0))
        attendance_rate = float(request.form.get('attendance_rate', 95.0))
        backlogs        = int(request.form.get('backlogs', 0))
        fee_due         = float(request.form.get('fee_due', 0.0))
        assignment_rate = float(request.form.get('assignment_rate', 100.0))
        lab_marks       = float(request.form.get('lab_marks', 100.0))

        # ── Validations ────────────────────────────────────────────────────
        if not student_id:
            return jsonify({'success': False, 'message': 'Student Roll ID is required.'}), 400
        if not name:
            return jsonify({'success': False, 'message': 'Full Name is required.'}), 400
        if not email:
            return jsonify({'success': False, 'message': 'Email address is required.'}), 400

        if Student.query.filter_by(student_id=student_id).first():
            return jsonify({'success': False, 'message': f'Roll ID "{student_id}" already exists.'}), 400

        if Student.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': f'Email "{email}" is already registered.'}), 400

        if not (0.0 <= current_gpa <= 10.0):
            return jsonify({'success': False, 'message': 'Current GPA must be between 0 and 10.'}), 400

        if not (0.0 <= prev_gpa <= 10.0):
            return jsonify({'success': False, 'message': 'Previous GPA must be between 0 and 10.'}), 400

        if not (0.0 <= assignment_rate <= 100.0):
            return jsonify({'success': False, 'message': 'Assignment rate must be between 0 and 100.'}), 400

        if not (0.0 <= lab_marks <= 100.0):
            return jsonify({'success': False, 'message': 'Lab score must be between 0 and 100.'}), 400

        if phone:
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
            if not clean_phone.isdigit() or len(clean_phone) < 8:
                return jsonify({'success': False, 'message': 'Phone number is invalid.'}), 400

        # ── Create student ─────────────────────────────────────────────────
        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            gender=gender,
            department_id=department_id,
            semester=semester,
            current_gpa=current_gpa,
            prev_gpa=prev_gpa,
            attendance_rate=attendance_rate,
            backlogs=backlogs,
            fee_due=fee_due,
            assignment_rate=assignment_rate,
            lab_marks=lab_marks
        )
        db.session.add(student)
        db.session.flush()  # populate student.id

        # Default fee record
        fee = Fees(
            student_id=student.id,
            total_fee=150000.0,
            paid_amount=150000.0 - fee_due,
            due_amount=fee_due,
            payment_status='Paid' if fee_due == 0 else ('Unpaid' if fee_due >= 150000.0 else 'Partial'),
            due_date=datetime.utcnow()
        )
        db.session.add(fee)

        # Run AI prediction immediately
        from ml_model.predict import predict_student_risk
        from models import process_student_risk_updates

        features = {
            'current_gpa': current_gpa,
            'prev_gpa': prev_gpa,
            'attendance_rate': attendance_rate,
            'backlogs': backlogs,
            'fee_due': fee_due,
            'assignment_rate': assignment_rate,
            'lab_marks': lab_marks,
            'semester': semester,
            'gpa_trend': current_gpa - prev_gpa,
            'counseling_count': 0
        }
        pred_res = predict_student_risk(features)
        process_student_risk_updates(student, pred_res)

        # Audit log
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Add Student",
            target_table="students",
            details=f"Added student {name} ({student_id}) — {pred_res['risk_level']} risk.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'✅ Student <strong>{name}</strong> registered successfully! '
                       f'AI Prediction: <strong>{pred_res["risk_level"]} Risk</strong>.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@student_bp.route('/students/edit/<int:id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_student(id):
    try:
        student = Student.query.get_or_404(id)
        
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        department_id = int(request.form.get('department_id'))
        semester = int(request.form.get('semester'))
        
        current_gpa = float(request.form.get('current_gpa', 0.0))
        prev_gpa = float(request.form.get('prev_gpa', 0.0))
        attendance_rate = float(request.form.get('attendance_rate', 95.0))
        backlogs = int(request.form.get('backlogs', 0))
        fee_due = float(request.form.get('fee_due', 0.0))
        assignment_rate = float(request.form.get('assignment_rate', 100.0))
        lab_marks = float(request.form.get('lab_marks', 100.0))
        
        # Validate GPA
        if not (0.0 <= current_gpa <= 10.0):
            flash("GPA must be between 0-10.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Previous GPA
        if not (0.0 <= prev_gpa <= 10.0):
            flash("Previous GPA must be between 0-10.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Assignment Rate
        if not (0.0 <= assignment_rate <= 100.0):
            flash("Assignment rate must be between 0-100.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Lab Score
        if not (0.0 <= lab_marks <= 100.0):
            flash("Lab score must be between 0-100.", "danger")
            return redirect(url_for('student.list_students'))
            
        # Validate Phone
        if phone:
            clean_phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
            if not clean_phone.isdigit() or len(clean_phone) < 8:
                flash("Phone number invalid.", "danger")
                return redirect(url_for('student.list_students'))
                
        # Validate duplicate email
        if email:
            existing_email = Student.query.filter_by(email=email).first()
            if existing_email and existing_email.id != id:
                flash("Email already registered.", "danger")
                return redirect(url_for('student.list_students'))
                
        # Trends detection: calculate trend relative to old values
        old_gpa = student.current_gpa
        old_risk_level = student.risk_level
        
        # Update attributes
        student.name = name
        student.email = email
        student.phone = phone
        student.gender = gender
        student.department_id = department_id
        student.semester = semester
        student.current_gpa = current_gpa
        student.prev_gpa = prev_gpa
        student.attendance_rate = attendance_rate
        student.backlogs = backlogs
        student.fee_due = fee_due
        student.assignment_rate = assignment_rate
        student.lab_marks = lab_marks
        
        # Update fee due amount
        fee_log = Fees.query.filter_by(student_id=student.id).first()
        if fee_log:
            fee_log.due_amount = student.fee_due
            fee_log.paid_amount = fee_log.total_fee - student.fee_due
            fee_log.payment_status = 'Paid' if student.fee_due == 0 else ('Unpaid' if student.fee_due >= fee_log.total_fee else 'Partial')
            
        # Run prediction immediately on update
        from ml_model.predict import predict_student_risk
        from models import process_student_risk_updates
        
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
        
        pred_res = predict_student_risk(features)
        process_student_risk_updates(student, pred_res, old_risk_level=old_risk_level, old_gpa=old_gpa)
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Edit Student",
            target_table="students",
            details=f"Edited student {student.name} ({student.student_id}). Updated prediction: {pred_res['risk_level']} risk.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"Student details updated. Prediction re-run complete: {pred_res['risk_level']} Risk.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating student: {str(e)}", "danger")
        
    return redirect(url_for('student.list_students'))

@student_bp.route('/students/delete/<int:id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_student(id):
    try:
        student = Student.query.get_or_404(id)
        name = student.name
        student_id = student.student_id
        
        db.session.delete(student)
        
        # Log Audit
        audit = AuditLog(
            user_id=session.get('user_id'),
            action="Delete Student",
            target_table="students",
            details=f"Deleted student {name} ({student_id}).",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f"Student {name} deleted successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting student: {str(e)}", "danger")
        
    return redirect(url_for('student.list_students'))

@student_bp.route('/students/profile/<int:id>', methods=['GET'])
@login_required
def view_profile(id):
    student = Student.query.get_or_404(id)
    counselings = Counseling.query.filter_by(student_id=student.id).order_by(Counseling.scheduled_date.desc()).all()
    predictions = Prediction.query.filter_by(student_id=student.id).order_by(Prediction.predicted_at.desc()).all()
    
    return render_template('student_profile.html',
                           student=student,
                           counselings=counselings,
                           predictions=predictions)

@student_bp.route('/api/students-list')
@login_required
def api_students_list():
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'student_id': s.student_id,
        'risk_level': s.risk_level
    } for s in students])

