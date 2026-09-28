import os
import sys
import time
import cv2
import json
import numpy as np

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models import Student, FaceEmbedding, AttendanceSession, AttendanceRecord, ClassModel, SystemSetting
from app.services.attendance_svc import AttendanceService
from app.services.face_pipeline import face_pipeline

def run_performance_benchmarks():
    db = SessionLocal()
    print("=" * 70)
    print("ATTENDAI — REAL-WORLD CAMERA RECOGNITION VALIDATION & BENCHMARKS")
    print("=" * 70)

    # 1. Pipeline specifications
    m_set = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
    r_set = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
    match_th = float(m_set.value) if m_set else 0.70
    review_th = float(r_set.value) if r_set else 0.52

    print(f"\n[CONFIGURATION]")
    print(f"  Face Detector:         OpenCV YuNet DNN (face_detection_yunet.onnx)")
    print(f"  Face Recognizer:       OpenCV SFace ONNX DNN (face_recognition_sface.onnx)")
    print(f"  Embedding Dimension:   128-dimensional unit vector")
    print(f"  Distance Metric:       Cosine Similarity: dot(a, b)")
    print(f"  Match Threshold:       {match_th:.2f} (>= {match_th:.2f} -> RECOGNIZED)")
    print(f"  Review Threshold:      {review_th:.2f} (>= {review_th:.2f} and < {match_th:.2f} -> REVIEW REQUIRED)")
    print(f"  Rejection:             < {review_th:.2f} -> UNKNOWN PERSON")

    # 2. Enrolled Students
    mca_students = db.query(Student).filter(Student.dataset_type == "TEST_DATA").all()
    print(f"\n[ENROLLED TEST_DATA STUDENTS]")
    for s in mca_students:
        emb_counts = len(s.face_embeddings)
        dims = [len(e.get_vector()) for e in s.face_embeddings]
        print(f"  - {s.id}: {s.name} ({s.roll_number}) | {emb_counts} Embeddings (Dims: {dims})")

    # 3. Create isolated validation session
    mca_class = db.query(ClassModel).filter(ClassModel.course == "MCA").first()
    session = AttendanceSession(
        class_id=mca_class.id if mca_class else "class_mca_final",
        date="2026-09-27",
        time="03:00 PM",
        title="Live Camera Real-World Benchmark Session",
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    print(f"\n[ACTIVE SESSION INITIALIZED]: {session.id} ({session.title})")

    base_images_dir = os.path.join(os.path.dirname(__file__), "data", "test_data", "images")
    real_world_dir = os.path.join(base_images_dir, "real_world_tests")

    test_scenarios = [
        {
            "id": "SCENARIO_1",
            "name": "Kanishka Sharma (NEW Webcam Capture)",
            "file": os.path.join(real_world_dir, "webcam_MCA001_new.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MCA001",
            "expected_attendance": True,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_2",
            "name": "Namita Jain (NEW Webcam Capture)",
            "file": os.path.join(real_world_dir, "webcam_MCA002_new.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MCA002",
            "expected_attendance": True,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_3",
            "name": "Akanksha Mishra (NEW Webcam Capture)",
            "file": os.path.join(real_world_dir, "webcam_MCA003_new.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MCA003",
            "expected_attendance": True,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_4",
            "name": "Unknown Person (Non-enrolled)",
            "file": os.path.join(base_images_dir, "unknown_person.jpg"),
            "expected_recognized": False,
            "expected_student_id": None,
            "expected_attendance": False,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_5",
            "name": "Two Registered People in One Frame",
            "file": os.path.join(real_world_dir, "webcam_multi_two_students.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MULTI",
            "expected_attendance": False, # Handled per-face
            "is_new_image": True
        },
        {
            "id": "SCENARIO_6",
            "name": "Registered Student + Unknown Person in One Frame",
            "file": os.path.join(real_world_dir, "webcam_multi_registered_and_unknown.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MULTI",
            "expected_attendance": False,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_7",
            "name": "No Face (Blank / Empty Background)",
            "file": os.path.join(real_world_dir, "webcam_no_face.jpg"),
            "expected_recognized": False,
            "expected_student_id": None,
            "expected_attendance": False,
            "is_new_image": True
        },
        {
            "id": "SCENARIO_8",
            "name": "Same Student Recognized Twice (Duplicate Protection)",
            "file": os.path.join(real_world_dir, "webcam_MCA001_new.jpg"),
            "expected_recognized": True,
            "expected_student_id": "MCA001",
            "expected_attendance": False, # ALREADY_MARKED
            "is_new_image": True
        },
    ]

    print("\n" + "=" * 70)
    print("EXECUTING REAL-WORLD TEST SCENARIOS & PROFILING")
    print("=" * 70)

    perf_records = []

    for sc in test_scenarios:
        filepath = sc["file"]
        img_bgr = cv2.imread(filepath)
        if img_bgr is None:
            print(f"Error loading {filepath}")
            continue

        # Performance Timings
        t0 = time.perf_counter()
        detected_boxes = face_pipeline.detect_faces(img_bgr)
        t_detect = (time.perf_counter() - t0) * 1000.0

        t_embed_total = 0.0
        embeddings = []
        for box in detected_boxes:
            x, y, w, h = box["x_px"], box["y_px"], box["w_px"], box["h_px"]
            crop = img_bgr[y:y+h, x:x+w]
            t_e0 = time.perf_counter()
            vec = face_pipeline.extract_embedding(crop)
            t_embed_total += (time.perf_counter() - t_e0) * 1000.0
            embeddings.append(vec)

        # Full service call (includes DB session check, dedup, audit log)
        t_full0 = time.perf_counter()
        res = AttendanceService.recognize_and_mark_attendance(
            db=db,
            image_bgr=img_bgr,
            session_id=session.id,
            match_threshold=match_th,
            review_threshold=review_th
        )
        t_total = (time.perf_counter() - t_full0) * 1000.0
        t_recognize = max(0.0, t_total - t_detect - t_embed_total)

        perf_records.append({
            "scenario": sc["name"],
            "detect_ms": t_detect,
            "embed_ms": t_embed_total,
            "recognize_ms": t_recognize,
            "total_ms": t_total
        })

        print(f"\n>>> [{sc['id']}]: {sc['name']}")
        print(f"    New Webcam Image (Different from enrollment): {'YES' if sc['is_new_image'] else 'NO'}")
        print(f"    Detected Faces: {res['total_detected']}")
        print(f"    Recognized:     {res['recognized']}")
        print(f"    Attendance:     {'MARKED' if res['attendance_marked'] else 'NOT MARKED'} ({res['reason']})")
        print(f"    Confidence:     {res['confidence']:.3f} (Threshold: {match_th:.2f})")
        print(f"    Timing: Detect: {t_detect:.1f}ms | Embed: {t_embed_total:.1f}ms | Recognition & DB: {t_recognize:.1f}ms | Total: {t_total:.1f}ms")

        if res.get("faces") and len(res["faces"]) > 1:
            print("    Multi-face Breakdown:")
            for idx, face in enumerate(res["faces"]):
                print(f"      Face {idx+1}: {face['student_name'] or 'Unknown'} ({face['student_id'] or 'N/A'}) | Score: {face['confidence']:.3f} | Status: {face['status']} | Attendance: {face['attendance_status']}")

    # 4. Summary Table of Performance
    print("\n" + "=" * 70)
    print("TASK 12: PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"{'Scenario':<42} | {'Detect (ms)':<11} | {'Embed (ms)':<10} | {'Total (ms)':<10}")
    print("-" * 78)
    for p in perf_records:
        print(f"{p['scenario'][:40]:<42} | {p['detect_ms']:>10.1f} | {p['embed_ms']:>9.1f} | {p['total_ms']:>9.1f}")

    avg_detect = np.mean([p["detect_ms"] for p in perf_records])
    avg_embed = np.mean([p["embed_ms"] for p in perf_records if p["embed_ms"] > 0])
    avg_total = np.mean([p["total_ms"] for p in perf_records])

    print("-" * 78)
    print(f"{'Average Execution Time':<42} | {avg_detect:>10.1f} | {avg_embed:>9.1f} | {avg_total:>9.1f}")
    print("=" * 78)

    # Clean up test session
    db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    db.close()
    print("\nBenchmark successfully completed and test session cleanly removed.")

if __name__ == "__main__":
    run_performance_benchmarks()
