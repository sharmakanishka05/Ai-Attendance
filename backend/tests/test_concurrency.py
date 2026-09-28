import concurrent.futures
import pytest

def test_concurrent_attendance_confirmation_safety(client, admin_headers):
    """
    Phase 10: Simulate concurrent attendance confirmation requests arriving
    at nearly the same time for the same (session_id, student_id).
    Verify:
    1. Exactly one AttendanceRecord per (session_id, student_id) is created.
    2. No duplicate records.
    3. Session status remains consistent and completed.
    """
    classes = client.get("/api/classes", headers=admin_headers).json()
    class_id = classes[0]["id"]

    # 1. Create a fresh session
    sess_res = client.post("/api/sessions", json={
        "class_id": class_id,
        "date": "2026-09-20",
        "time": "10:30 AM",
        "title": "Concurrency Safety Test Session"
    }, headers=admin_headers)
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    # Grab a student
    students = client.get(f"/api/students?class_name={classes[0]['name']}", headers=admin_headers).json()
    student = students[0]
    student_id = student["id"]

    payload_a = {
        "session_id": session_id,
        "items": [
            {"student_id": student_id, "status": "present", "confidence": 0.95, "marked_method": "ai_upload"}
        ],
        "notes": "Thread A submission"
    }

    payload_b = {
        "session_id": session_id,
        "items": [
            {"student_id": student_id, "status": "present", "confidence": 0.96, "marked_method": "ai_upload"}
        ],
        "notes": "Thread B submission"
    }

    results = []

    def submit_confirm(payload):
        return client.post("/api/attendance/confirm", json=payload, headers=admin_headers)

    # Execute concurrent POSTs
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(submit_confirm, payload_a),
            executor.submit(submit_confirm, payload_b)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # At least one (or both with safe upsert/dedup) succeeded, neither caused server error 500
    for res in results:
        assert res.status_code in [200, 400]

    # Verify session detail: EXACTLY 1 record for this student
    detail_res = client.get(f"/api/sessions/{session_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    session_data = detail_res.json()
    records = session_data["records"]
    student_records = [r for r in records if r["student_id"] == student_id]

    assert len(student_records) == 1, f"Expected exactly 1 attendance record, found {len(student_records)}"
    assert session_data["status"] == "completed"
