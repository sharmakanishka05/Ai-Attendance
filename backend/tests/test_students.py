def test_get_students_list(client, admin_headers):
    res = client.get("/api/students", headers=admin_headers)
    assert res.status_code == 200
    students = res.json()
    assert len(students) == 3
    assert any(s["roll_number"] == "MCA001" for s in students)

def test_create_student_and_duplicate_rejection(client, admin_headers):
    student_payload = {
        "name": "Test Unique Student",
        "roll_number": "MCA999",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year",
        "email": "test.unique@kit.ac.in"
    }
    # First create
    res1 = client.post("/api/students", json=student_payload, headers=admin_headers)
    assert res1.status_code == 200
    created = res1.json()
    assert created["roll_number"] == "MCA999"

    # Duplicate roll number attempt
    res2 = client.post("/api/students", json=student_payload, headers=admin_headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_get_student_detail(client, admin_headers):
    res = client.get("/api/students", headers=admin_headers)
    assert res.status_code == 200
    student_id = res.json()[0]["id"]

    detail_res = client.get(f"/api/students/{student_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert "stats" in data
    assert "rate" in data["stats"]
    assert "history" in data

def test_delete_biometric_face_data_privacy(client, admin_headers):
    # Find student with face data
    students_res = client.get("/api/students", headers=admin_headers)
    assert students_res.status_code == 200
    students = students_res.json()
    target = next((s for s in students if s["has_face_data"]), None)
    assert target is not None

    del_res = client.delete(f"/api/students/{target['id']}/face-data", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify student still exists, but has_face_data is False
    check_res = client.get(f"/api/students/{target['id']}", headers=admin_headers)
    assert check_res.status_code == 200
    assert check_res.json()["has_face_data"] is False
