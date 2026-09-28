import os
import cv2
import json
import pytest
import numpy as np
from app.models import Student, FaceEmbedding, AttendanceRecord, AttendanceSession, User, ClassModel
from app.seed_test_data import seed_mca_test_data, reset_mca_test_data

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_data", "images")

def load_test_image_bytes(filename: str) -> bytes:
    filepath = os.path.join(TEST_DATA_DIR, filename)
    assert os.path.exists(filepath), f"File not found: {filepath}"
    with open(filepath, "rb") as f:
        return f.read()

def test_manifest_structure_and_integrity():
    """
    Verifies test_manifest.json conforms to the required specification and all image files exist.
    """
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_manifest.json")
    assert os.path.exists(manifest_path), "backend/data/test_manifest.json does not exist"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["dataset"] == "MCA_ATTENDANCE_TEST_DATA"
    assert manifest["dataset_type"] == "TEST_DATA"
    assert len(manifest["students"]) == 3
    
    expected_students = {
        "MCA001": ("Kanishka Sharma", "IMAGE_1", "MCA001_Kanishka_Sharma.jpg"),
        "MCA002": ("Namita Jain", "IMAGE_2", "MCA002_Namita_Jain.jpg"),
        "MCA003": ("Akanksha Mishra", "IMAGE_3", "MCA003_Akanksha_Mishra.jpg")
    }
    
    for s in manifest["students"]:
        sid = s["student_id"]
        assert sid in expected_students
        exp_name, exp_img, exp_file = expected_students[sid]
        assert s["name"] == exp_name
        assert s["course"] == "MCA"
        assert s["year"] == "Final Year"
        assert s["expected_image"] == exp_img
        
        # Verify physical file exists
        full_img_path = os.path.join(TEST_DATA_DIR, exp_file)
        assert os.path.exists(full_img_path), f"Image file missing: {full_img_path}"

def test_recognition_image_1_mca001_kanishka_sharma(client, teacher_headers):
    """
    Image 1 -> MCA001 -> Kanishka Sharma
    Verifies actual recognition pipeline result, face detected, and identity match.
    """
    img_bytes = load_test_image_bytes("MCA001_Kanishka_Sharma.jpg")
    files = {"file": ("image_1.jpg", img_bytes, "image/jpeg")}
    
    # 1. Test via standard process-image endpoint
    res = client.post("/api/attendance/process-image", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_detected"] >= 1
    assert data["recognized_count"] >= 1
    
    recognized_face = next((f for f in data["faces"] if f["status"] == "recognized"), None)
    assert recognized_face is not None
    assert recognized_face["student_id"] == "MCA001"
    assert recognized_face["student_name"] == "Kanishka Sharma"
    assert recognized_face["confidence"] >= 0.70

def test_recognition_image_2_mca002_namita_jain(client, teacher_headers):
    """
    Image 2 -> MCA002 -> Namita Jain
    Verifies actual recognition pipeline result, face detected, and identity match.
    """
    img_bytes = load_test_image_bytes("MCA002_Namita_Jain.jpg")
    files = {"file": ("image_2.jpg", img_bytes, "image/jpeg")}
    
    res = client.post("/api/attendance/process-image", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_detected"] >= 1
    assert data["recognized_count"] >= 1
    
    recognized_face = next((f for f in data["faces"] if f["status"] == "recognized"), None)
    assert recognized_face is not None
    assert recognized_face["student_id"] == "MCA002"
    assert recognized_face["student_name"] == "Namita Jain"
    assert recognized_face["confidence"] >= 0.70

def test_recognition_image_3_mca003_akanksha_mishra(client, teacher_headers):
    """
    Image 3 -> MCA003 -> Akanksha Mishra
    Verifies actual recognition pipeline result, face detected, and identity match.
    """
    img_bytes = load_test_image_bytes("MCA003_Akanksha_Mishra.jpg")
    files = {"file": ("image_3.jpg", img_bytes, "image/jpeg")}
    
    res = client.post("/api/attendance/process-image", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_detected"] >= 1
    assert data["recognized_count"] >= 1
    
    recognized_face = next((f for f in data["faces"] if f["status"] == "recognized"), None)
    assert recognized_face is not None
    assert recognized_face["student_id"] == "MCA003"
    assert recognized_face["student_name"] == "Akanksha Mishra"
    assert recognized_face["confidence"] >= 0.70

def test_attendance_marking_all_three_students(client, teacher_headers, db_session):
    """
    When registered TEST_DATA students are recognized:
    face_detected = True
    recognized = True
    student_id = corresponding student
    attendance_marked = True
    """
    # Create a fresh session for this test
    mca_class = db_session.query(ClassModel).filter(ClassModel.course == "MCA").first()
    sess_res = client.post("/api/sessions", json={
        "class_id": mca_class.id if mca_class else "class_mca_final",
        "date": "2026-09-27",
        "time": "10:00 AM",
        "title": "Live MCA Attendance Marking Session"
    }, headers=teacher_headers)
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    test_cases = [
        ("MCA001_Kanishka_Sharma.jpg", "MCA001", "Kanishka Sharma"),
        ("MCA002_Namita_Jain.jpg", "MCA002", "Namita Jain"),
        ("MCA003_Akanksha_Mishra.jpg", "MCA003", "Akanksha Mishra"),
    ]

    for img_file, expected_id, expected_name in test_cases:
        img_bytes = load_test_image_bytes(img_file)
        files = {"file": (img_file, img_bytes, "image/jpeg")}
        data = {"session_id": session_id}
        
        res = client.post("/api/attendance/recognize-and-mark", files=files, data=data, headers=teacher_headers)
        assert res.status_code == 200
        payload = res.json()
        
        assert payload["face_detected"] is True, f"Face not detected for {expected_id}"
        assert payload["recognized"] is True, f"Not recognized for {expected_id}"
        assert payload["student_id"] == expected_id, f"Expected {expected_id}, got {payload['student_id']}"
        assert payload["student_name"] == expected_name
        assert payload["attendance_marked"] is True, f"Attendance not marked for {expected_id}"
        assert payload["confidence"] >= 0.70

    # Complete session
    sess_obj = db_session.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    sess_obj.status = "completed"
    db_session.commit()

def test_duplicate_attendance_protection(client, teacher_headers, db_session):
    """
    Tests duplicate-attendance prevention:
    First recognition:
      attendance_marked = True
    Second recognition in same session:
      attendance_marked = False
      reason = "ALREADY_MARKED"
    """
    mca_class = db_session.query(ClassModel).filter(ClassModel.course == "MCA").first()
    sess_res = client.post("/api/sessions", json={
        "class_id": mca_class.id if mca_class else "class_mca_final",
        "date": "2026-09-28",
        "time": "11:00 AM",
        "title": "Duplicate Prevention Test Session"
    }, headers=teacher_headers)
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    img_bytes = load_test_image_bytes("MCA001_Kanishka_Sharma.jpg")
    files1 = {"file": ("kanishka_first.jpg", img_bytes, "image/jpeg")}
    data1 = {"session_id": session_id}

    # 1. First recognition -> marked
    res1 = client.post("/api/attendance/recognize-and-mark", files=files1, data=data1, headers=teacher_headers)
    assert res1.status_code == 200
    p1 = res1.json()
    assert p1["face_detected"] is True
    assert p1["recognized"] is True
    assert p1["student_id"] == "MCA001"
    assert p1["attendance_marked"] is True

    # 2. Second recognition with the same student in the same session -> rejected as ALREADY_MARKED
    files2 = {"file": ("kanishka_second.jpg", img_bytes, "image/jpeg")}
    data2 = {"session_id": session_id}
    res2 = client.post("/api/attendance/recognize-and-mark", files=files2, data=data2, headers=teacher_headers)
    assert res2.status_code == 200
    p2 = res2.json()
    assert p2["face_detected"] is True
    assert p2["recognized"] is True
    assert p2["student_id"] == "MCA001"
    assert p2["attendance_marked"] is False
    assert p2["reason"] == "ALREADY_MARKED"

    # Verify database has exactly 1 record for this student in this session
    records = db_session.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id,
        AttendanceRecord.student_id == "MCA001"
    ).all()
    assert len(records) == 1

    # Cleanly complete session
    sess_obj = db_session.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    sess_obj.status = "completed"
    db_session.commit()

def test_unknown_person(client, teacher_headers):
    """
    Unknown person test case:
    Image of an unknown person (not enrolled in MCA test data):
    face_detected = True
    recognized = False
    student_id = None
    attendance_marked = False
    reason = "UNKNOWN_PERSON"
    """
    img_bytes = load_test_image_bytes("unknown_person.jpg")
    files = {"file": ("unknown.jpg", img_bytes, "image/jpeg")}
    
    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    p = res.json()
    
    assert p["face_detected"] is True
    assert p["recognized"] is False
    assert p["student_id"] is None
    assert p["attendance_marked"] is False
    assert p["reason"] == "UNKNOWN_PERSON"

def test_no_face_image(client, teacher_headers):
    """
    No face test case:
    Image containing no face:
    face_detected = False
    recognized = False
    attendance_marked = False
    The application must not crash.
    """
    # Create a plain blank image (no faces)
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", blank_img)
    files = {"file": ("blank.jpg", buf.tobytes(), "image/jpeg")}
    
    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    p = res.json()
    
    assert p["face_detected"] is False
    assert p["recognized"] is False
    assert p["attendance_marked"] is False
    assert p["reason"] == "NO_FACE_DETECTED"

def test_test_data_isolation_and_safe_reset(db_session):
    """
    Verifies that safe reset operation deletes ONLY TEST_DATA records,
    and NEVER deletes production students, production users, or production embeddings.
    """
    # Check baseline counts
    prod_students_count = db_session.query(Student).filter(Student.dataset_type != "TEST_DATA").count()
    prod_users_count = db_session.query(User).count()
    assert prod_users_count >= 2, f"Expected at least 2 users, found {prod_users_count}"

    # Perform Safe Reset
    reset_report = reset_mca_test_data(db_session)
    assert reset_report["students_deleted"] == 3
    assert reset_report["embeddings_deleted"] >= 3

    # Verify TEST_DATA students are gone
    test_students = db_session.query(Student).filter(Student.dataset_type == "TEST_DATA").all()
    assert len(test_students) == 0

    # Verify PRODUCTION data is completely untouched
    prod_students_after = db_session.query(Student).filter(Student.dataset_type != "TEST_DATA").count()
    prod_users_after = db_session.query(User).count()
    assert prod_students_after == prod_students_count
    assert prod_users_after == prod_users_count

    # Re-seed test data to restore state
    seed_report = seed_mca_test_data(db_session)
    assert seed_report["students_created"] == 3
    assert seed_report["embeddings_created"] >= 3

def test_seed_repeatability_avoids_duplicates(db_session):
    """
    Verifies repeatable seed process:
    Running seed multiple times updates existing records without creating duplicates.
    """
    initial_count = db_session.query(Student).filter(Student.dataset_type == "TEST_DATA").count()
    assert initial_count == 3

    # Run seed second time
    report = seed_mca_test_data(db_session)
    assert report["students_created"] == 0
    assert report["students_updated"] == 3
    assert report["embeddings_created"] == 0
    assert report["embeddings_updated"] >= 3

    # Total TEST_DATA student count must strictly remain 3
    final_count = db_session.query(Student).filter(Student.dataset_type == "TEST_DATA").count()
    assert final_count == 3
