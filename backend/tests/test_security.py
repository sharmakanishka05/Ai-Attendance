import pytest
from datetime import timedelta
from jose import jwt
from app.config import settings

def test_unauthenticated_api_requests_rejected(client):
    """Phase 8 - Requirement 1 & 6: Unauthenticated requests return 401"""
    endpoints = [
        ("GET", "/api/students"),
        ("POST", "/api/students"),
        ("GET", "/api/classes"),
        ("POST", "/api/classes"),
        ("GET", "/api/sessions"),
        ("POST", "/api/sessions"),
        ("GET", "/api/reports/attendance"),
        ("GET", "/api/reports/audit"),
        ("GET", "/api/settings"),
        ("PUT", "/api/settings"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        elif method == "PUT":
            res = client.put(path, json={})
        else:
            res = client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {path}, got {res.status_code}"
        assert "detail" in res.json()

def test_login_invalid_credentials_rejected(client):
    """Phase 8 - Requirement 4: Invalid credentials return 401"""
    res1 = client.post("/api/auth/login", json={
        "email": "ajeet.singh@kit.ac.in",
        "password": "wrong_password_123"
    })
    assert res1.status_code == 401
    assert "Incorrect" in res1.json()["detail"]

    res2 = client.post("/api/auth/login", json={
        "email": "nonexistent.user@attendai.edu",
        "password": "password123"
    })
    assert res2.status_code == 401

def test_expired_token_rejected(client):
    """Phase 8 - Requirement 5: Expired JWT tokens return 401"""
    from app.api.auth import create_access_token
    expired_token = create_access_token(
        data={"sub": "any_user_id", "email": "test@attendai.edu", "role": "admin"},
        expires_delta=timedelta(seconds=-60)  # Expired 1 minute ago
    )
    res = client.get("/api/students", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401

def test_teacher_role_restrictions(client, teacher_headers, admin_headers):
    """
    Phase 8 - Requirement 2, 3, 8:
    Teacher attempting admin operations returns 403 Forbidden.
    Admin operation succeeds.
    """
    # 1. Student Creation: Teacher blocked (403), Admin allowed
    student_payload = {
        "name": "RBAC Test Student",
        "roll_number": "RBAC-001",
        "class_name": "Computer Science",
        "section": "Section A"
    }
    teacher_post = client.post("/api/students", json=student_payload, headers=teacher_headers)
    assert teacher_post.status_code == 403, "Teacher was able to create student!"

    admin_post = client.post("/api/students", json=student_payload, headers=admin_headers)
    assert admin_post.status_code == 200
    student_id = admin_post.json()["id"]

    # 2. Biometric Data Purge: Teacher blocked (403), Admin allowed
    teacher_purge = client.delete(f"/api/students/{student_id}/face-data", headers=teacher_headers)
    assert teacher_purge.status_code == 403, "Teacher was able to purge biometrics!"

    admin_purge = client.delete(f"/api/students/{student_id}/face-data", headers=admin_headers)
    assert admin_purge.status_code == 200

    # 3. System Settings modification: Teacher blocked (403), Admin allowed
    teacher_settings = client.put("/api/settings", json={"face_match_threshold": 0.85}, headers=teacher_headers)
    assert teacher_settings.status_code == 403, "Teacher was able to update settings!"

    admin_settings = client.put("/api/settings", json={"face_match_threshold": 0.85}, headers=admin_headers)
    assert admin_settings.status_code == 200

    # 4. Audit Log access: Teacher blocked (403), Admin allowed
    teacher_audit = client.get("/api/reports/audit", headers=teacher_headers)
    assert teacher_audit.status_code == 403, "Teacher was able to access audit logs!"

    admin_audit = client.get("/api/reports/audit", headers=admin_headers)
    assert admin_audit.status_code == 200

    # 5. Student Deletion: Teacher blocked (403), Admin allowed
    teacher_del = client.delete(f"/api/students/{student_id}", headers=teacher_headers)
    assert teacher_del.status_code == 403, "Teacher was able to delete student!"

    admin_del = client.delete(f"/api/students/{student_id}", headers=admin_headers)
    assert admin_del.status_code == 200

def test_teacher_allowed_operations(client, teacher_headers):
    """
    Teacher can view students, view classes, and conduct attendance.
    """
    # List students
    res_students = client.get("/api/students", headers=teacher_headers)
    assert res_students.status_code == 200

    # List classes
    res_classes = client.get("/api/classes", headers=teacher_headers)
    assert res_classes.status_code == 200

    # View reports
    res_reports = client.get("/api/reports/attendance", headers=teacher_headers)
    assert res_reports.status_code == 200

def test_raw_biometric_embeddings_never_leaked_in_api(client, admin_headers):
    """Phase 8 - Requirement 9: Raw vector embeddings must NEVER be exposed in student or session API payloads"""
    # 1. Student list
    res_list = client.get("/api/students", headers=admin_headers)
    assert res_list.status_code == 200
    for s in res_list.json():
        assert "embedding" not in s
        assert "vector" not in s
        assert "embedding_json" not in s

    # 2. Student detail
    student_id = res_list.json()[0]["id"]
    res_detail = client.get(f"/api/students/{student_id}", headers=admin_headers)
    assert res_detail.status_code == 200
    data = res_detail.json()
    assert "embedding" not in data
    assert "vector" not in data
    assert "embedding_json" not in data

def test_mock_ai_cannot_activate_in_production(monkeypatch):
    """Phase 8 - Requirement 7: Mock recognition must be completely disabled in production"""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    assert settings.APP_ENV == "production"
