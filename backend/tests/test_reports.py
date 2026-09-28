def test_get_attendance_report(client, admin_headers):
    res = client.get("/api/reports/attendance", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "attendance_rate" in data
    assert "present_count" in data
    assert "trend" in data
    assert len(data["trend"]) > 0

def test_export_csv_download(client, admin_headers):
    res = client.get("/api/reports/export-csv", headers=admin_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    csv_text = res.text
    # Verify expected headers
    assert "Roll Number" in csv_text
    assert "Student Name" in csv_text
    assert "Attendance Rate" in csv_text
    # Verify student entries exist in CSV
    assert "MCA001" in csv_text

def test_export_excel_download(client, admin_headers):
    res = client.get("/api/reports/export-excel", headers=admin_headers)
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert len(res.content) > 1000  # Non-empty valid binary XLSX
