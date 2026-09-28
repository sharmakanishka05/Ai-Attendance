import os
import time
import pytest
from app.models import AttendanceSession, AttendanceRecord, ClassModel

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_data", "images")
REAL_WORLD_DIR = os.path.join(TEST_DATA_DIR, "real_world_tests")

def load_real_world_bytes(filename: str) -> bytes:
    filepath = os.path.join(REAL_WORLD_DIR, filename)
    assert os.path.exists(filepath), f"File not found: {filepath}"
    with open(filepath, "rb") as f:
        return f.read()

def test_kanishka_new_webcam_image_recognition(client, teacher_headers):
    """
    TASK 11.1: Kanishka using a NEW webcam image (different from enrollment image).
    Cosine similarity must satisfy FACE_MATCH_THRESHOLD >= 0.70.
    """
    img_bytes = load_real_world_bytes("webcam_MCA001_new.jpg")
    files = {"file": ("kanishka_webcam.jpg", img_bytes, "image/jpeg")}
    
    start_t = time.perf_counter()
    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    total_ms = (time.perf_counter() - start_t) * 1000.0

    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["recognized"] is True
    assert data["student_id"] == "MCA001"
    assert data["student_name"] == "Kanishka Sharma"
    assert data["confidence"] >= 0.70
    # Must be a realistic score on a new image (not an exact 1.000 duplicate)
    assert data["confidence"] <= 0.999
    assert total_ms < 2000.0, f"Processing took too long: {total_ms:.1f}ms"

def test_namita_new_webcam_image_recognition(client, teacher_headers):
    """
    TASK 11.2: Namita using a NEW webcam image (different from enrollment image).
    Cosine similarity must satisfy FACE_MATCH_THRESHOLD >= 0.70.
    """
    img_bytes = load_real_world_bytes("webcam_MCA002_new.jpg")
    files = {"file": ("namita_webcam.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["recognized"] is True
    assert data["student_id"] == "MCA002"
    assert data["student_name"] == "Namita Jain"
    assert data["confidence"] >= 0.70

def test_akanksha_new_webcam_image_recognition(client, teacher_headers):
    """
    TASK 11.3: Akanksha using a NEW webcam image (different from enrollment image).
    Cosine similarity must satisfy FACE_MATCH_THRESHOLD >= 0.70.
    """
    img_bytes = load_real_world_bytes("webcam_MCA003_new.jpg")
    files = {"file": ("akanksha_webcam.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["recognized"] is True
    assert data["student_id"] == "MCA003"
    assert data["student_name"] == "Akanksha Mishra"
    assert data["confidence"] >= 0.70

def test_unknown_person_camera_rejection(client, teacher_headers):
    """
    TASK 11.4: Unknown person must be rejected with NO attendance.
    """
    filepath = os.path.join(TEST_DATA_DIR, "unknown_person.jpg")
    with open(filepath, "rb") as f:
        img_bytes = f.read()

    files = {"file": ("unknown_camera.jpg", img_bytes, "image/jpeg")}
    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["recognized"] is False
    assert data["student_id"] is None
    assert data["attendance_marked"] is False
    assert data["reason"] == "UNKNOWN_PERSON"

def test_two_registered_students_in_single_frame(client, teacher_headers):
    """
    TASK 11.5: Two registered students in one camera frame.
    Processes each face independently.
    """
    img_bytes = load_real_world_bytes("webcam_multi_two_students.jpg")
    files = {"file": ("two_students.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["total_detected"] >= 2
    assert "faces" in data
    assert len(data["faces"]) >= 2

    recognized_ids = {f["student_id"] for f in data["faces"] if f["status"] == "recognized"}
    assert "MCA001" in recognized_ids
    assert "MCA002" in recognized_ids

def test_registered_plus_unknown_person_in_single_frame(client, teacher_headers):
    """
    TASK 11.6: Registered student + unknown person in one camera frame.
    Enrolled student is recognized; unknown person is rejected with no attendance.
    """
    img_bytes = load_real_world_bytes("webcam_multi_registered_and_unknown.jpg")
    files = {"file": ("multi_registered_unknown.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is True
    assert data["total_detected"] >= 2

    faces = data["faces"]
    known_face = next((f for f in faces if f["student_id"] == "MCA001"), None)
    unknown_face = next((f for f in faces if f["status"] == "unknown"), None)

    assert known_face is not None, "Registered student MCA001 should be detected"
    assert known_face["status"] == "recognized"
    assert known_face["confidence"] >= 0.70

    assert unknown_face is not None, "Unknown face should be detected independently"
    assert unknown_face["student_id"] is None
    assert unknown_face["attendance_marked"] is False
    assert unknown_face["status"] == "unknown"

def test_no_face_webcam_frame(client, teacher_headers):
    """
    TASK 11.7: No face camera frame.
    Gracefully handled with NO_FACE_DETECTED and no crash.
    """
    img_bytes = load_real_world_bytes("webcam_no_face.jpg")
    files = {"file": ("no_face.jpg", img_bytes, "image/jpeg")}

    res = client.post("/api/attendance/recognize-and-mark", files=files, headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["face_detected"] is False
    assert data["recognized"] is False
    assert data["attendance_marked"] is False
    assert data["reason"] == "NO_FACE_DETECTED"

def test_same_student_recognized_twice_in_session(client, teacher_headers, db_session):
    """
    TASK 11.8: Same student recognized twice in the same session.
    First -> attendance marked
    Second -> rejected as ALREADY_MARKED
    """
    mca_class = db_session.query(ClassModel).filter(ClassModel.course == "MCA").first()
    sess_res = client.post("/api/sessions", json={
        "class_id": mca_class.id if mca_class else "class_mca_final",
        "date": "2026-09-29",
        "time": "09:00 AM",
        "title": "Camera Duplicate Prevention Validation"
    }, headers=teacher_headers)
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    img_bytes = load_real_world_bytes("webcam_MCA001_new.jpg")
    files = {"file": ("webcam1.jpg", img_bytes, "image/jpeg")}
    data = {"session_id": session_id}

    # First attempt: attendance marked
    res1 = client.post("/api/attendance/recognize-and-mark", files=files, data=data, headers=teacher_headers)
    assert res1.status_code == 200
    p1 = res1.json()
    assert p1["recognized"] is True
    assert p1["attendance_marked"] is True
    assert p1["student_id"] == "MCA001"

    # Second attempt: ALREADY_MARKED
    files2 = {"file": ("webcam2.jpg", img_bytes, "image/jpeg")}
    res2 = client.post("/api/attendance/recognize-and-mark", files=files2, data=data, headers=teacher_headers)
    assert res2.status_code == 200
    p2 = res2.json()
    assert p2["recognized"] is True
    assert p2["attendance_marked"] is False
    assert p2["reason"] == "ALREADY_MARKED"
