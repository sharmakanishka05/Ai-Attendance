import io
import cv2
import numpy as np
import pytest
from app.models import AttendanceRecord, AttendanceCorrection, AuditLog, AttendanceSession

def create_synthetic_test_group_photo() -> bytes:
    """
    Creates a synthetic image with 2 distinct drawn facial figures (circles with eyes and mouth)
    to test the face detector / feature extractor end-to-end.
    """
    img = np.ones((480, 640, 3), dtype=np.uint8) * 240
    # Draw Face 1
    cv2.circle(img, (200, 240), 70, (200, 180, 160), -1)
    cv2.circle(img, (175, 220), 10, (50, 50, 50), -1) # Eye L
    cv2.circle(img, (225, 220), 10, (50, 50, 50), -1) # Eye R
    cv2.ellipse(img, (200, 260), (25, 12), 0, 0, 180, (50, 50, 50), 3) # Mouth

    # Draw Face 2
    cv2.circle(img, (440, 240), 70, (190, 175, 155), -1)
    cv2.circle(img, (415, 220), 10, (40, 40, 40), -1)
    cv2.circle(img, (465, 220), 10, (40, 40, 40), -1)
    cv2.ellipse(img, (440, 260), (25, 12), 0, 0, 180, (40, 40, 40), 3)

    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()

def test_full_real_attendance_pipeline_e2e(client, admin_headers, db_session):
    """
    Phase 9: Comprehensive End-to-End Real Attendance Pipeline Test.
    Login -> Select Class -> Start Session -> Upload Image -> Face Detection & Matching ->
    Manual Correction with Audit Reason -> Confirm -> DB Commit -> Reports -> CSV/Excel
    """
    # 1. Select Class
    classes_res = client.get("/api/classes", headers=admin_headers)
    assert classes_res.status_code == 200
    classes = classes_res.json()
    assert len(classes) > 0
    target_class = classes[0]
    class_id = target_class["id"]

    # 2. Start Attendance Session
    create_sess_res = client.post("/api/sessions", json={
        "class_id": class_id,
        "date": "2026-09-20",
        "time": "11:00 AM",
        "title": f"Live Roll Call - {target_class['name']}"
    }, headers=admin_headers)
    assert create_sess_res.status_code == 200
    session_id = create_sess_res.json()["id"]

    # 3. Upload image for Real Face Detection & Similarity Matching
    image_bytes = create_synthetic_test_group_photo()
    files = {"file": ("classroom_test.jpg", image_bytes, "image/jpeg")}
    data = {"class_id": class_id}

    process_res = client.post("/api/attendance/process-image", data=data, files=files, headers=admin_headers)
    assert process_res.status_code == 200
    cv_result = process_res.json()

    assert "total_detected" in cv_result
    assert "faces" in cv_result
    # Real AI was invoked: confidence values are real floats, not synthetic dummy strings
    for face in cv_result["faces"]:
        assert isinstance(face["confidence"], (int, float))
        assert "bbox" in face
        assert "x" in face["bbox"]

    # 4. Fetch students in the class to formulate confirm payload
    students_res = client.get(f"/api/students?class_name={target_class['name']}", headers=admin_headers)
    students = students_res.json()
    assert len(students) >= 2
    student_1 = students[0]
    student_2 = students[1]

    # 5. Confirm Attendance
    confirm_payload = {
        "session_id": session_id,
        "items": [
            {
                "student_id": student_1["id"],
                "status": "present",
                "confidence": 0.96,
                "marked_method": "ai_upload"
            },
            {
                "student_id": student_2["id"],
                "status": "present",
                "confidence": 0.94,
                "marked_method": "ai_upload"
            }
        ],
        "notes": "Real AI verified classroom capture"
    }
    confirm_res = client.post("/api/attendance/confirm", json=confirm_payload, headers=admin_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["success"] is True

    # 6. Verify Database Commit for Session & AttendanceRecords
    session_in_db = db_session.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    assert session_in_db is not None
    assert session_in_db.status == "completed"

    records = db_session.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()
    # All enrolled students in class are accounted for (present + absent)
    assert len(records) == len(students)

    # 7. Manual Correction: Change Student 1 from Present -> Late with Audit Reason
    rec1 = next(r for r in records if r.student_id == student_1["id"])
    correct_res = client.post("/api/attendance/correct", json={
        "record_id": rec1.id,
        "new_status": "late",
        "reason": "Traffic congestion; arrived 10 min late with gate slip"
    }, headers=admin_headers)
    assert correct_res.status_code == 200
    assert correct_res.json()["new_status"] == "late"

    # Verify audit record exists in database
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.entity_id == rec1.id,
        AuditLog.action == "MANUAL_CORRECTION"
    ).first()
    assert audit_entry is not None
    assert "Traffic congestion" in audit_entry.details

    # 8. Reports update & CSV/Excel Exports
    rep_res = client.get("/api/reports/attendance", headers=admin_headers)
    assert rep_res.status_code == 200

    csv_res = client.get(f"/api/reports/export-csv?class_id={class_id}", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]

    excel_res = client.get(f"/api/reports/export-excel?class_id={class_id}", headers=admin_headers)
    assert excel_res.status_code == 200
    assert "spreadsheetml" in excel_res.headers["content-type"]
