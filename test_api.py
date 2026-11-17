
from datetime import date, datetime, time, timedelta
import os
import tempfile


def make_model(model_class, **values):
    
    instance = model_class()
    for field_name, value in values.items():
        setattr(instance, field_name, value)
    return instance


def run_tests():
    with tempfile.TemporaryDirectory(prefix="emp-api-test-") as temp_dir:
        os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(temp_dir, "test.db")

        from config import Config
        from sqlalchemy.pool import NullPool

        Config.SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
                                                                                  
        Config.SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}

        from app import create_app
        from extensions import db, login_manager
        from models.user import User
        from models.course import Course
        from models.timeline import SystemTimeline
        from models.rubric import ExaminationRubric
        from services.evaluation_service import submit_evaluation
        from werkzeug.security import generate_password_hash

        app = create_app()
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
                                                                                
        login_manager.session_protection = "basic"
        client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()

            admin = make_model(
                User,
                full_name="Test Administrator",
                email="admin@test.local",
                password_hash=generate_password_hash("Admin1234"),
                role="admin",
                is_approved=True,
                account_active=True,
            )
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id

        def as_user(user_id):
            with client.session_transaction() as session:
                session.clear()
                session["_user_id"] = str(user_id)
                session["_fresh"] = True

        def check(response, expected, label):
            assert response.status_code == expected, (
                f"{label}: expected HTTP {expected}, got {response.status_code}: "
                f"{response.get_data(as_text=True)[:500]}"
            )
            print(f"PASS {label}: HTTP {expected}")
            return response

                                                                                      
        unauth_response = check(client.get("/api/examinations/"), 401, "API authentication")
        assert unauth_response.headers.get("X-Frame-Options") == "SAMEORIGIN"
        print("PASS Browser security headers")

        as_user(admin_id)

                                                                   
        with client.session_transaction() as session:
            session["_user_id"] = str(admin_id)
            session["_fresh"] = True
        check(client.post("/auth/logout"), 400, "HTML CSRF protection")

                                                  
        with app.app_context():
            course = make_model(Course, course_name="API Testing", course_code="APITEST")
            db.session.add(course)
            db.session.commit()
            course_id = course.id

        check(client.post("/api/examinations/", json={
            "exam_name": "Invalid Marks Exam",
            "course_id": course_id,
            "total_marks": 0,
            "passing_marks": 5,
        }), 400, "Examination backend validation")

        created_exam = check(client.post("/api/examinations/", json={
            "exam_name": "API Integration Exam",
            "course_id": course_id,
            "total_marks": 100,
            "passing_marks": 40,
            "status": "Draft",
        }), 201, "Examination POST").get_json()
        exam_id = created_exam["id"]
        check(client.get("/api/examinations/"), 200, "Examination GET list")
        check(client.get(f"/api/examinations/{exam_id}"), 200, "Examination GET detail")
        check(client.put(f"/api/examinations/{exam_id}", json={
            "exam_name": "Updated API Integration Exam",
            "status": "Slot Creation",
        }), 200, "Examination PUT")
        disposable_exam = check(client.post("/api/examinations/", json={
            "exam_name": "Disposable API Exam",
            "course_id": course_id,
            "total_marks": 50,
            "passing_marks": 20,
            "status": "Draft",
        }), 201, "Disposable Examination POST").get_json()
        check(client.delete(f"/api/examinations/{disposable_exam['id']}"), 200, "Examination DELETE")

                                                                          
        examiner = check(client.post("/api/examiners/", json={
            "full_name": "API Examiner",
            "email": "examiner@test.local",
            "password": "Examiner123",
        }), 201, "Examiner POST").get_json()
        examiner_id = examiner["id"]
        check(client.get("/api/examiners/"), 200, "Examiner GET list")
        check(client.get(f"/api/examiners/{examiner_id}"), 200, "Examiner GET detail")
        check(client.put(f"/api/examiners/{examiner_id}", json={
            "is_approved": True, "full_name": "Updated API Examiner",
        }), 200, "Examiner PUT/approve")
        check(client.delete(f"/api/examiners/{examiner_id}"), 200, "Examiner DELETE/deactivate")
        as_user(examiner_id)
        check(client.get("/api/slots/"), 403, "Deactivated examiner access restriction")
        as_user(admin_id)
        check(client.put(f"/api/examiners/{examiner_id}", json={
            "is_active": True,
        }), 200, "Examiner PUT/reactivate")

                                                                 
        student = check(client.post("/api/students/", json={
            "full_name": "API Student",
            "email": "student@test.local",
            "password": "Student123",
        }), 201, "Student POST").get_json()
        student_id = student["id"]
        check(client.get("/api/students/"), 200, "Student GET list")
        check(client.get(f"/api/students/{student_id}"), 200, "Student GET detail")
        check(client.put(f"/api/students/{student_id}", json={
            "full_name": "Updated API Student",
        }), 200, "Student PUT")
        check(client.delete(f"/api/students/{student_id}"), 200, "Student DELETE/deactivate")
        as_user(student_id)
        check(client.get("/api/examinations/"), 403, "Deactivated student access restriction")
        as_user(admin_id)
        check(client.put(f"/api/students/{student_id}", json={
            "is_active": True,
        }), 200, "Student PUT/reactivate")
        second_student = check(client.post("/api/students/", json={
            "full_name": "Capacity Test Student",
            "email": "capacity-student@test.local",
            "password": "Capacity123",
        }), 201, "Second Student POST").get_json()
        second_student_id = second_student["id"]

                                                                          
        with app.app_context():
            draft = Course.query.filter_by(id=course_id).first()
            from models.examination import Examination
            draft_exam = make_model(
                Examination,
                exam_name="Hidden Draft",
                course_id=course_id,
                total_marks=50,
                passing_marks=20,
                status="Draft",
            )
            db.session.add(draft_exam)
            db.session.commit()
            draft_id = draft_exam.id

        as_user(student_id)
        visible = check(client.get("/api/examinations/"), 200, "Student examination list").get_json()
        assert all(item["id"] != draft_id for item in visible), "Student API exposed a draft examination"
        check(client.get(f"/api/examinations/{draft_id}"), 404, "Student draft detail restriction")

                                                           
        with app.app_context():
            db.session.add(make_model(
                SystemTimeline,
                setting_name="student_booking",
                start_datetime=datetime.now() - timedelta(days=1),
                end_datetime=datetime.now() + timedelta(days=10),
                is_active=True,
            ))
            db.session.commit()

                                                                                          
        as_user(admin_id)
        capacity_exam = check(client.post("/api/examinations/", json={
            "exam_name": "Capacity and Rubric Test",
            "course_id": course_id,
            "total_marks": 10,
            "passing_marks": 5,
            "status": "Booking Open",
        }), 201, "Capacity Examination POST").get_json()
        capacity_slot = check(client.post("/api/slots/", json={
            "examination_id": capacity_exam["id"],
            "examiner_id": examiner_id,
            "slot_date": (date.today() + timedelta(days=4)).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
            "capacity": 1,
        }), 201, "Single-capacity Slot POST").get_json()
        check(client.post("/api/slots/", json={
            "examination_id": capacity_exam["id"],
            "examiner_id": examiner_id,
            "slot_date": (date.today() + timedelta(days=5)).isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
            "capacity": 0,
        }), 400, "Slot capacity validation")

        as_user(student_id)
        capacity_booking = check(client.post("/api/bookings/", json={
            "slot_id": capacity_slot["id"],
        }), 201, "Capacity Booking POST").get_json()
        as_user(second_student_id)
        check(client.post("/api/bookings/", json={
            "slot_id": capacity_slot["id"],
        }), 400, "Slot over-capacity rejection")

        with app.app_context():
            rubric = make_model(
                ExaminationRubric,
                examination_id=capacity_exam["id"],
                rubric_name="Practical Skill",
                description="Test rubric",
                max_marks=10,
            )
            db.session.add(rubric)
            db.session.commit()
            rubric_id = rubric.id
            ok, message = submit_evaluation(
                capacity_booking["id"], examiner_id, {rubric_id: 11}, "Over limit"
            )
            assert not ok, "Evaluation service accepted marks above rubric maximum"
            print("PASS Rubric maximum-mark validation")
            ok, message = submit_evaluation(
                capacity_booking["id"], examiner_id, {rubric_id: 8}, "Valid score"
            )
            assert ok, f"Evaluation service rejected a valid score: {message}"
            print("PASS Valid rubric evaluation")

                                                                            
        as_user(admin_id)
        tomorrow = date.today() + timedelta(days=1)
        slot_data = {
            "examination_id": exam_id,
            "examiner_id": examiner_id,
            "slot_date": tomorrow.isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "capacity": 2,
        }
        slot = check(client.post("/api/slots/", json=slot_data), 201, "Slot POST").get_json()
        slot_id = slot["id"]
        check(client.get("/api/slots/"), 200, "Slot GET list")
        check(client.get(f"/api/slots/{slot_id}"), 200, "Slot GET detail")
        check(client.put(f"/api/slots/{slot_id}", json={
            "capacity": 3,
        }), 200, "Slot PUT")
        disposable_slot = check(client.post("/api/slots/", json={
            **slot_data, "slot_date": (tomorrow + timedelta(days=5)).isoformat(),
            "start_time": "14:00", "end_time": "15:00",
        }), 201, "Second Slot POST").get_json()
        check(client.delete(f"/api/slots/{disposable_slot['id']}"), 200, "Slot DELETE")

                                                                
        second_slot = check(client.post("/api/slots/", json={
            **slot_data, "slot_date": (tomorrow + timedelta(days=1)).isoformat(),
            "start_time": "10:00", "end_time": "11:00",
        }), 201, "Reschedule Slot POST").get_json()

                                                                                              
        as_user(student_id)
        booking = check(client.post("/api/bookings/", json={
            "slot_id": slot_id,
        }), 201, "Booking POST").get_json()
        booking_id = booking["id"]
        check(client.post("/api/bookings/", json={"slot_id": slot_id}), 400, "Duplicate booking validation")
        check(client.get("/api/bookings/"), 200, "Booking GET list")
        check(client.get(f"/api/bookings/{booking_id}"), 200, "Booking GET detail")

        as_user(admin_id)
        check(client.put(f"/api/bookings/{booking_id}", json={
            "slot_id": second_slot["id"],
        }), 200, "Booking PUT/reschedule")

        as_user(student_id)
        check(client.post("/api/bookings/", json={"slot_id": slot_id}), 400, "Duplicate examination booking validation")
        check(client.delete(f"/api/bookings/{booking_id}"), 200, "Booking DELETE/cancel")

                                                                                  
        check(client.get("/api/students/"), 403, "Student role restriction")
        check(client.post("/api/examinations/", json={}), 403, "Student write restriction")

                                                                                     
        as_user(examiner_id)
        check(client.get("/api/slots/"), 200, "Examiner slot list")
        check(client.get("/api/students/"), 403, "Examiner admin-resource restriction")
        examiner_dashboard = check(client.get("/examiner/dashboard"), 200, "Examiner dashboard and chart data")
        assert b"evaluationChart" in examiner_dashboard.data and b"participantChart" in examiner_dashboard.data

        as_user(student_id)
        student_dashboard = check(client.get("/student/dashboard"), 200, "Student dashboard and chart data")
        assert b"historyChart" in student_dashboard.data and b"statusChart" in student_dashboard.data and b"resultChart" in student_dashboard.data

        as_user(admin_id)
        admin_dashboard = check(client.get("/admin/dashboard"), 200, "Admin dashboard and chart data")
        assert b"completionChart" in admin_dashboard.data and b"examinerChart" in admin_dashboard.data
        with client.session_transaction() as session:
            csrf = session.get("_csrf_token")
        check(client.post("/auth/logout", data={"csrf_token": csrf}), 302, "CSRF-protected logout")

        print("\\nAll isolated API and dashboard integration checks passed.")

                                                                                   
                                                                              
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

                                                                        
        close_client = getattr(client, "close", None)
        if callable(close_client):
            close_client()
        

if __name__ == "__main__":
    run_tests()
