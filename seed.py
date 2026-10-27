import os
from datetime import datetime, date, timedelta
from app import create_app
from models import db, User, Department, Student, Fees, Marks, Prediction, Alert, Counseling, AuditLog, ParentNotification, Assignment, Notification, Attendance, DailyAttendance

def seed_database():
    app = create_app()
    with app.app_context():
        print("Re-creating all database tables...")
        db.drop_all()
        db.create_all()
        
        print("Seeding departments...")
        cse = Department(name="Computer Science Engineering", code="CSE")
        ece = Department(name="Electronics & Communication Engineering", code="ECE")
        mech = Department(name="Mechanical Engineering", code="MECH")
        civil = Department(name="Civil Engineering", code="CIVIL")
        
        db.session.add_all([cse, ece, mech, civil])
        db.session.flush() # Populate IDs
        
        print("Seeding staff user accounts...")
        # Admin
        admin = User(username="admin", email="admin@college.edu", role="Admin", full_name="Dr. Tarun Kumar")
        admin.set_password("admin123")
        
        # Mentor
        mentor = User(username="mentor", email="mentor@college.edu", role="Mentor", full_name="Prof. S. R. Sharma")
        mentor.set_password("mentor123")
        
        # Counselor
        counselor = User(username="counselor", email="counselor@college.edu", role="Counselor", full_name="Dr. Anjali Mehta")
        counselor.set_password("counselor123")
        
        # Principal
        principal = User(username="principal", email="principal@college.edu", role="Principal", full_name="Dr. Ramesh Rao")
        principal.set_password("principal123")
        
        # Faculty / Lecturer
        faculty = User(username="faculty", email="faculty@college.edu", role="Faculty", full_name="Dr. Sarah Connor")
        faculty.set_password("faculty123")
        
        db.session.add_all([admin, mentor, counselor, principal, faculty])
        db.session.flush()
        
        print("Seeding student profiles with different risk levels...")
        # 1. High Risk Student (Poor GPA, backlogs, fee due)
        s1 = Student(
            student_id="CSE-2025-001", name="Rohan Sharma", email="rohan@student.com", phone="+91 9876543210",
            gender="Male", department_id=cse.id, semester=3, current_gpa=4.2, prev_gpa=5.8, backlogs=4, fee_due=120000.0,
            assignment_rate=45.0, lab_marks=50.0,
            risk_score=94.2, risk_level="High", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="Academic: Student has 4 active backlogs. Academic: Low GPA of 4.20 (below 6.0 standard). Academic: Declining grade trend (GPA dropped by 1.60 recently)."
        )
        
        # 2. High Risk Student (Successfully counseled - has before-vs-after improvement data)
        # We start with s2 being "Low" risk current state, but has a "Completed" counseling record reflecting their previous "High" risk state.
        s2 = Student(
            student_id="ECE-2025-012", name="Priya Patel", email="priya@student.com", phone="+91 9876543211",
            gender="Female", department_id=ece.id, semester=5, current_gpa=7.2, prev_gpa=5.8, backlogs=0, fee_due=0.0,
            assignment_rate=92.0, lab_marks=86.0,
            risk_score=12.5, risk_level="Low", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="None: Student demonstrates healthy academic performance."
        )

        # 3. Medium Risk Student (Average grades, backlogs, fee outstanding)
        s3 = Student(
            student_id="ME-2025-003", name="Amit Verma", email="amit@student.com", phone="+91 9876543212",
            gender="Male", department_id=mech.id, semester=2, current_gpa=6.8, prev_gpa=7.2, backlogs=1, fee_due=50000.0,
            assignment_rate=72.0, lab_marks=68.0,
            risk_score=48.2, risk_level="Medium", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="Academic: Student has 1 active backlog. Financial: High unpaid fees (Rs. 50,000). Academic: Declining grade trend."
        )

        # 4. Medium Risk Student (Low GPA, backlogs)
        s4 = Student(
            student_id="CIVIL-2025-009", name="Vikram Singh", email="vikram@student.com", phone="+91 9876543213",
            gender="Male", department_id=civil.id, semester=4, current_gpa=5.1, prev_gpa=6.1, backlogs=3, fee_due=0.0,
            assignment_rate=78.0, lab_marks=70.0,
            risk_score=52.0, risk_level="Medium", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="Academic: Student has 3 active backlogs. Academic: Low GPA of 5.10 (below 6.0 standard)."
        )

        # 5. Low Risk Student (Excellent academics)
        s5 = Student(
            student_id="CSE-2025-025", name="Neha Gupta", email="neha@student.com", phone="+91 9876543214",
            gender="Female", department_id=cse.id, semester=3, current_gpa=9.2, prev_gpa=9.1, backlogs=0, fee_due=0.0,
            assignment_rate=98.0, lab_marks=95.0,
            risk_score=3.5, risk_level="Low", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="None: Student demonstrates healthy academic performance."
        )

        # 6. Low Risk Student (Good stats)
        s6 = Student(
            student_id="ECE-2025-004", name="Rahul Nair", email="rahul@student.com", phone="+91 9876543215",
            gender="Male", department_id=ece.id, semester=5, current_gpa=8.1, prev_gpa=8.0, backlogs=0, fee_due=0.0,
            assignment_rate=92.0, lab_marks=86.0,
            risk_score=7.8, risk_level="Low", predicted_at=datetime.utcnow() - timedelta(hours=2),
            reasons="None: Student demonstrates healthy academic performance."
        )

        # Add more students to have a realistic count (Total 12 students)
        students_extra = [
            Student(student_id="CSE-2025-006", name="Arjun Sen", email="arjun@student.com", phone="+91 9876543216", gender="Male", department_id=cse.id, semester=3, current_gpa=7.5, prev_gpa=7.2, backlogs=0, fee_due=0.0, assignment_rate=88.0, lab_marks=80.0, risk_score=11.2, risk_level="Low", reasons="None: Student demonstrates healthy academic performance."),
            Student(student_id="ECE-2025-008", name="Sneha Reddy", email="sneha@student.com", phone="+91 9876543217", gender="Female", department_id=ece.id, semester=5, current_gpa=7.9, prev_gpa=7.8, backlogs=0, fee_due=0.0, assignment_rate=90.0, lab_marks=84.0, risk_score=8.5, risk_level="Low"),
            Student(student_id="ME-2025-015", name="Kabir Khan", email="kabir@student.com", phone="+91 9876543218", gender="Male", department_id=mech.id, semester=2, current_gpa=5.9, prev_gpa=6.5, backlogs=1, fee_due=100000.0, assignment_rate=74.0, lab_marks=72.0, risk_score=36.4, risk_level="Medium", reasons="Academic: Low GPA of 5.90. Financial: High unpaid fees."),
            Student(student_id="CIVIL-2025-002", name="Ananya Rao", email="ananya@student.com", phone="+91 9876543219", gender="Female", department_id=civil.id, semester=4, current_gpa=7.4, prev_gpa=7.4, backlogs=0, fee_due=50000.0, assignment_rate=85.0, lab_marks=78.0, risk_score=14.5, risk_level="Low"),
            Student(student_id="CSE-2025-018", name="Dev Patel", email="dev@student.com", phone="+91 9876543220", gender="Male", department_id=cse.id, semester=1, current_gpa=6.1, prev_gpa=7.5, backlogs=2, fee_due=120000.0, assignment_rate=65.0, lab_marks=60.0, risk_score=78.2, risk_level="High", reasons="Academic: Student has 2 active backlogs. Financial: High unpaid fees. Academic: Declining GPA trend."),
            Student(student_id="ME-2025-007", name="Karan Joshi", email="karan@student.com", phone="+91 9876543221", gender="Male", department_id=mech.id, semester=6, current_gpa=7.0, prev_gpa=7.0, backlogs=0, fee_due=0.0, assignment_rate=85.0, lab_marks=80.0, risk_score=9.1, risk_level="Low")
        ]
        
        all_students = [s1, s2, s3, s4, s5, s6] + students_extra
        for student in all_students:
            student.set_password("student123")
            
        db.session.add_all(all_students)
        db.session.flush() # Populate IDs for linking records
        
        # Seed marks
        print("Seeding marks...")
        subjects_by_dept = {
            cse.id: ["Data Structures", "Computer Organization", "Discrete Mathematics"],
            ece.id: ["Digital Electronics", "Network Analysis", "Signals & Systems"],
            mech.id: ["Thermodynamics", "Fluid Mechanics", "Material Science"],
            civil.id: ["Surveying", "Structural Analysis", "Geotechnical Eng"]
        }
        
        for student in all_students:
            subjects = subjects_by_dept.get(student.department_id, ["General Studies"])
            for sub in subjects:
                # Seed internal marks
                # Low risk gets high marks, high risk gets low marks
                if student.risk_level == "High":
                    marks_val = 40 + (student.id % 15)
                    sem_val = 4.2
                elif student.risk_level == "Medium":
                    marks_val = 55 + (student.id % 20)
                    sem_val = 5.8
                else:
                    marks_val = 80 + (student.id % 18)
                    sem_val = 7.8
                    
                db.session.add(Marks(student_id=student.id, subject=sub, marks_obtained=marks_val, max_marks=100.0, exam_type="Internal"))
                db.session.add(Marks(student_id=student.id, subject=sub, marks_obtained=sem_val * 10, max_marks=100.0, exam_type="Semester"))
        
        # Seed assignments
        print("Seeding assignments...")
        for student in all_students:
            subjects = subjects_by_dept.get(student.department_id, ["General Studies"])
            for i, sub in enumerate(subjects):
                status = "Completed"
                if student.risk_level == "High" and i == 0:
                    status = "Pending"
                elif student.risk_level == "Medium" and i == 1:
                    status = "Pending"
                db.session.add(Assignment(
                    student_id=student.id,
                    title=f"Assignment {i+1} on {sub}",
                    subject=sub,
                    due_date=datetime.utcnow() - timedelta(days=i),
                    status=status,
                    marks_obtained=75.0 if status == "Completed" else None
                ))
        
        # Seed subject attendance
        print("Seeding subject attendance...")
        for student in all_students:
            subjects = subjects_by_dept.get(student.department_id, ["General Studies"])
            for sub in subjects:
                att_pct = student.attendance_rate if student.attendance_rate else 85.0
                attended = int((att_pct / 100.0) * 50)
                db.session.add(Attendance(student_id=student.id, subject=sub, total_classes=50, attended_classes=attended, percentage=att_pct))
                
                # Daily attendance entries
                db.session.add(DailyAttendance(student_id=student.id, subject=sub, date=date.today() - timedelta(days=1), status='Absent' if student.risk_level == 'High' else 'Present', marked_by="Dr. Sarah Connor"))

        # Seed parent notification logs (academic warning logs)
        print("Seeding parent notification logs...")
        db.session.add_all([
            ParentNotification(
                student_id=s1.id,
                student_name=s1.name,
                parent_phone="+91 9988776655",
                parent_email="parent.rohan@email.com",
                notification_type="Absence Warning",
                date_time=datetime.utcnow() - timedelta(days=2),
                status="Sent",
                message="ABSENCE NOTICE: Student Rohan Sharma (Roll No: CSE-2025-001) was marked ABSENT for lecture 'Data Structures' on 2026-08-02. Lecturer: Dr. Sarah Connor.",
                channel="Email & SMS"
            ),
            ParentNotification(
                student_id=s3.id,
                student_name=s3.name,
                parent_phone="+91 8877665544",
                parent_email="parent.amit@email.com",
                notification_type="Risk Warning",
                date_time=datetime.utcnow() - timedelta(days=1),
                status="Sent",
                message="Dear Parent/Guardian, your ward Amit Verma (Roll No: ME-2025-003) has been identified with a Medium dropout risk level. Factors: low assignment rate and unpaid outstanding fees.",
                channel="Email & SMS"
            )
        ])
        
        # Seed mentor to student notifications
        print("Seeding mentor-to-student notifications...")
        db.session.add_all([
            Notification(student_id=s1.id, sender_id=mentor.id, message="Rohan, please meet me in the department tomorrow during lunch break regarding your performance checklist.", created_at=datetime.utcnow() - timedelta(hours=5)),
            Notification(student_id=s3.id, sender_id=mentor.id, message="Amit, remember that your Thermodynamics assignment is due this week. Submit it to avoid losing marks.", created_at=datetime.utcnow() - timedelta(days=2))
        ])
        
        # Seed fee details
        print("Seeding fee records...")
        db.session.add_all([
            Fees(student_id=s1.id, total_fee=150000.0, paid_amount=30000.0, due_amount=120000.0, payment_status="Partial", due_date=datetime.utcnow() + timedelta(days=15)),
            Fees(student_id=s2.id, total_fee=150000.0, paid_amount=150000.0, due_amount=0.0, payment_status="Paid"),
            Fees(student_id=s3.id, total_fee=150000.0, paid_amount=100000.0, due_amount=50000.0, payment_status="Partial", due_date=datetime.utcnow() + timedelta(days=15)),
            Fees(student_id=s4.id, total_fee=150000.0, paid_amount=150000.0, due_amount=0.0, payment_status="Paid"),
            Fees(student_id=s5.id, total_fee=150000.0, paid_amount=150000.0, due_amount=0.0, payment_status="Paid")
        ])
        
        # Seed prediction history
        print("Seeding prediction runs...")
        db.session.add_all([
            Prediction(student_id=s1.id, risk_score=94.2, risk_level="High", feature_importance_json='["Multiple Backlogs", "Low GPA", "Declining Trend"]', reasons_json='["Multiple Backlogs", "Low GPA", "Declining Trend"]'),
            Prediction(student_id=s2.id, risk_score=12.5, risk_level="Low", feature_importance_json='["None"]', reasons_json='["None"]'),
            Prediction(student_id=s3.id, risk_score=48.2, risk_level="Medium", feature_importance_json='["Fee Outstanding", "Declining Trend"]', reasons_json='["Fee Outstanding", "Declining Trend"]'),
            Prediction(student_id=s4.id, risk_score=52.0, risk_level="Medium", feature_importance_json='["Multiple Backlogs", "Low GPA"]', reasons_json='["Multiple Backlogs", "Low GPA"]'),
            Prediction(student_id=s5.id, risk_score=3.5, risk_level="Low", feature_importance_json='["None"]', reasons_json='["None"]')
        ])
        
        # Seed communication alerts
        print("Seeding communication alerts...")
        db.session.add_all([
            Alert(student_id=s1.id, message="System generated: Student Rohan Sharma is classified as High Risk. Reasons: Multiple Backlogs, Low GPA.", risk_level="High", status="Pending", notification_type="Email"),
            Alert(student_id=s3.id, message="System generated: Student Amit Verma is classified as Medium Risk. Reasons: Fee Outstanding, Declining GPA Trend.", risk_level="Medium", status="Pending", notification_type="SMS")
        ])
        
        # Seed counseling sessions with before-vs-after snapshot records
        print("Seeding counseling schedules...")
        db.session.add_all([
            # Pending scheduled meeting for Rohan Sharma with counselor Dr. Anjali Mehta
            Counseling(student_id=s1.id, counselor_id=counselor.id, scheduled_date=datetime.utcnow() + timedelta(days=2), status="Scheduled"),
            # Completed meeting for Priya Patel (s2) showing BEFORE metrics vs current AFTER metrics
            Counseling(
                student_id=s2.id, 
                counselor_id=counselor.id, 
                scheduled_date=datetime.utcnow() - timedelta(days=12), 
                status="Completed", 
                notes="Discussed backlog reduction and fee dues. Student completed assignments and marks improved.", 
                actions_taken="Arranged counseling sheet, set up weekly check-ins.",
                gpa_before=5.8,
                backlogs_before=3,
                assignment_before=50.0,
                risk_score_before=82.5,
                risk_level_before="High",
                internal_marks_before=55.0
            )
        ])
        
        # Seed audit logs
        print("Seeding audit logs...")
        db.session.add_all([
            AuditLog(user_id=admin.id, action="Create Database", target_table="all", details="Database initialized and tables created successfully.", ip_address="127.0.0.1"),
            AuditLog(user_id=admin.id, action="Seed Database", target_table="all", details="Seeded database with initial departments, staff accounts, and diverse student test records.", ip_address="127.0.0.1")
        ])
        
        db.session.commit()
        print("\nDatabase seeded successfully!")

if __name__ == '__main__':
    seed_database()
