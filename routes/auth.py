from flask import Blueprint, request, redirect, url_for, flash, session, g
from functools import wraps
from models import db, User, AuditLog

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'student_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        if 'user_id' in session:
            g.user = User.query.get(session['user_id'])
            if not g.user:
                session.clear()
                return redirect(url_for('auth.login'))
            g.student = None
        elif 'student_id' in session:
            from models import Student
            g.student = Student.query.get(session['student_id'])
            if not g.student:
                session.clear()
                return redirect(url_for('auth.login'))
            g.user = None
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session and 'student_id' not in session:
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                flash(f"Access Denied: You do not have permission to view this resource. Requires: {', '.join(roles)}", "danger")
                if user_role == 'Student':
                    return redirect(url_for('main.student_portal'))
                return redirect(url_for('main.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    if 'student_id' in session:
        return redirect(url_for('main.student_portal'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            # Log action
            log = AuditLog(
                user_id=user.id,
                action="User Login",
                details=f"User {username} logged in successfully.",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            if user.role == 'Faculty':
                return redirect(url_for('main.faculty_attendance'))
            return redirect(url_for('main.dashboard'))
        else:
            # Check student login
            from models import Student
            student = Student.query.filter_by(student_id=username).first()
            
            if student and student.check_password(password):
                session.clear()
                session['student_id'] = student.id
                session['username'] = student.student_id
                session['role'] = 'Student'
                session['full_name'] = student.name
                
                # Log action
                log = AuditLog(
                    user_id=None,
                    action="Student Login",
                    details=f"Student {student.name} logged in successfully.",
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()
                
                flash(f"Welcome to your academic portal, {student.name}!", "success")
                return redirect(url_for('main.student_portal'))
            
            # Audit failed attempt
            log = AuditLog(
                user_id=None,
                action="Failed Login Attempt",
                details=f"Failed login attempt for username: {username}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash("Invalid username or password.", "danger")
            
    # Simple templates fallback
    from flask import render_template
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('username')
    user_id = session.get('user_id')
    student_id = session.get('student_id')
    
    if user_id or student_id:
        log = AuditLog(
            user_id=user_id if user_id else None,
            action="User Logout",
            details=f"User {username} logged out.",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
        
    from models import Department
    departments = Department.query.all()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        phone = request.form.get('phone')
        
        # Validations
        if not full_name or not email or not username or not password or not confirm_password or not role:
            flash("All required fields must be filled.", "danger")
            from flask import render_template
            return render_template('register.html', departments=departments)
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            from flask import render_template
            return render_template('register.html', departments=departments)
            
        # Check duplicate username
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            from flask import render_template
            return render_template('register.html', departments=departments)
            
        # Check duplicate email
        if User.query.filter_by(email=email).first():
            flash("Email address already registered.", "danger")
            from flask import render_template
            return render_template('register.html', departments=departments)
            
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                role=role,
                full_name=full_name,
                phone=phone
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Log action
            log = AuditLog(
                user_id=None,
                action="User Registration",
                details=f"User {username} registered successfully as {role}.",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering user: {str(e)}", "danger")
            
    from flask import render_template
    return render_template('register.html', departments=departments)

