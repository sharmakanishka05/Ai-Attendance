def test_session_lifecycle_and_duplicate_prevention(client, admin_headers):
    classes = client.get("/api/classes", headers=admin_headers).json()
    assert len(classes) > 0
    class_id = classes[0]["id"]

    # 1. Create Session
    create_res = client.post("/api/sessions", json={
        "class_id": class_id,
        "date": "2026-09-20",
        "time": "09:00 AM",
        "title": "Automated Test Session"
    }, headers=admin_headers)
    assert create_res.status_code == 200
    session_id = create_res.json()["id"]

    students = client.get(f"/api/students?class_name={classes[0]['name']}", headers=admin_headers).json()
    student_1 = students[0]["id"]
    student_2 = students[1]["id"]

    # 2. Confirm Attendance with intentional duplicate entry for student_1
    confirm_payload = {
        "session_id": session_id,
        "items": [
            {"student_id": student_1, "status": "present", "confidence": 0.95, "marked_method": "ai_upload"},
            # Duplicate attempt for student_1 in same batch
            {"student_id": student_1, "status": "late", "confidence": 0.85, "marked_method": "manual"},
            {"student_id": student_2, "status": "present", "confidence": 0.92, "marked_method": "ai_upload"}
        ],
        "notes": "Testing duplicate prevention"
    }

    conf_res = client.post("/api/attendance/confirm", json=confirm_payload, headers=admin_headers)
    assert conf_res.status_code == 200
    assert conf_res.json()["success"] is True

    # 3. Verify session detail contains only 1 record per student
    detail_res = client.get(f"/api/sessions/{session_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    records = detail_res.json()["records"]
    s1_records = [r for r in records if r["student_id"] == student_1]
    assert len(s1_records) == 1, "Duplicate record was not prevented!"

    # 4. Manual Correction
    rec_id = s1_records[0]["record_id"]
    corr_res = client.post("/api/attendance/correct", json={
        "record_id": rec_id,
        "new_status": "late",
        "reason": "Student arrived 15 min late with permission"
    }, headers=admin_headers)
    assert corr_res.status_code == 200
    assert corr_res.json()["new_status"] == "late"
