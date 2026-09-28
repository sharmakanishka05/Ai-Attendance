import os
import sys
sys.path.insert(0, ".")
import cv2
import json
from app.db.database import SessionLocal
from app.models import Student, FaceEmbedding, AttendanceSession, AttendanceRecord, ClassModel, SystemSetting
from app.services.attendance_svc import AttendanceService
from app.services.face_pipeline import face_pipeline

def run_validation():
    db = SessionLocal()
    print("=" * 60)
    print("AI ATTENDANCE SYSTEM: END-TO-END VALIDATION SUITE")
    print("=" * 60)

    # 1. Model & Embedding Configuration
    print("\n--- Model & Architecture Diagnostics ---")
    m_set = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
    r_set = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
    match_th = float(m_set.value) if m_set else 0.70
    review_th = float(r_set.value) if r_set else 0.52
    print(f"Face Detector:      YuNet DNN (face_detection_yunet.onnx)")
    print(f"Face Recognizer:    SFace ONNX DNN (face_recognition_sface.onnx)")
    print(f"Match Threshold:    {match_th:.2f}")
    print(f"Review Threshold:   {review_th:.2f}")
    print(f"Comparison Metric:  Cosine Similarity")

    # Check enrolled MCA students
    mca_students = db.query(Student).filter(Student.dataset_type == "TEST_DATA").all()
    print(f"\nEnrolled TEST_DATA Students in DB: {len(mca_students)}")
    for s in mca_students:
        vecs = [len(e.get_vector()) for e in s.face_embeddings]
        print(f"  {s.id}: {s.name} ({s.roll_number}) | Course: {s.course} | Embeddings: {len(s.face_embeddings)} (dims: {vecs})")

    # 2. Test Image Recognition & Attendance Marking
    print("\n--- TASK 3: Real Image Recognition Test ---")
    test_dir = r"data\test_data\images"
    test_cases = [
        ("MCA001_Kanishka_Sharma.jpg", "MCA001", "Kanishka Sharma"),
        ("MCA002_Namita_Jain.jpg", "MCA002", "Namita Jain"),
        ("MCA003_Akanksha_Mishra.jpg", "MCA003", "Akanksha Mishra")
    ]

    # Create fresh active session
    mca_class = db.query(ClassModel).filter(ClassModel.course == "MCA").first()
    class_id = mca_class.id if mca_class else "class_mca_final"
    session = AttendanceSession(
        class_id=class_id,
        date="2026-09-27",
        time="02:30 PM",
        title="Validation Live Roll Call",
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    print(f"Created active attendance session: {session.id} ({session.title})")

    all_passed = True
    for fname, exp_id, exp_name in test_cases:
        fpath = os.path.join(test_dir, fname)
        img = cv2.imread(fpath)
        res = AttendanceService.recognize_and_mark_attendance(
            db=db,
            image_bgr=img,
            session_id=session.id,
            match_threshold=match_th,
            review_threshold=review_th
        )
        passed = (
            res["face_detected"] is True and
            res["recognized"] is True and
            res["student_id"] == exp_id and
            res["student_name"] == exp_name and
            res["attendance_marked"] is True and
            res["confidence"] >= match_th
        )
        status_str = "PASS" if passed else "FAIL"
        if not passed: all_passed = False
        print(f"  [{status_str}] {exp_id} ({exp_name}):")
        print(f"         detected={res['face_detected']}, recognized={res['recognized']}, confidence={res['confidence']:.3f}, attendance_marked={res['attendance_marked']}")

    # 3. TASK 4: Unknown Person Test
    print("\n--- TASK 4: Unknown Person Test ---")
    unk_path = os.path.join(test_dir, "unknown_person.jpg")
    unk_img = cv2.imread(unk_path)
    unk_res = AttendanceService.recognize_and_mark_attendance(
        db=db,
        image_bgr=unk_img,
        session_id=session.id,
        match_threshold=match_th,
        review_threshold=review_th
    )
    unk_passed = (
        unk_res["face_detected"] is True and
        unk_res["recognized"] is False and
        unk_res["student_id"] is None and
        unk_res["attendance_marked"] is False and
        unk_res["reason"] == "UNKNOWN_PERSON"
    )
    status_str = "PASS" if unk_passed else "FAIL"
    if not unk_passed: all_passed = False
    print(f"  [{status_str}] Unknown Person:")
    print(f"         face_detected={unk_res['face_detected']}, recognized={unk_res['recognized']}, student_id={unk_res['student_id']}, attendance_marked={unk_res['attendance_marked']}, reason={unk_res['reason']}, score={unk_res['confidence']}")

    # 4. TASK 5: Duplicate Attendance Test
    print("\n--- TASK 5: Duplicate Attendance Test ---")
    # Present MCA001 a second time in the same session
    dup_img = cv2.imread(os.path.join(test_dir, "MCA001_Kanishka_Sharma.jpg"))
    dup_res = AttendanceService.recognize_and_mark_attendance(
        db=db,
        image_bgr=dup_img,
        session_id=session.id,
        match_threshold=match_th,
        review_threshold=review_th
    )
    dup_passed = (
        dup_res["face_detected"] is True and
        dup_res["recognized"] is True and
        dup_res["student_id"] == "MCA001" and
        dup_res["attendance_marked"] is False and
        dup_res["reason"] == "ALREADY_MARKED"
    )
    status_str = "PASS" if dup_passed else "FAIL"
    if not dup_passed: all_passed = False
    print(f"  [{status_str}] Duplicate Recognition of MCA001:")
    print(f"         recognized={dup_res['recognized']}, attendance_marked={dup_res['attendance_marked']}, reason={dup_res['reason']}")

    # Verify database count
    mca1_recs = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == "MCA001"
    ).all()
    print(f"  Database count for (session, MCA001): {len(mca1_recs)} (strictly exactly 1)")

    # 5. TASK 6: No Face Test
    print("\n--- TASK 6: No Face Test ---")
    import numpy as np
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    no_face_res = AttendanceService.recognize_and_mark_attendance(
        db=db,
        image_bgr=blank_img,
        session_id=session.id,
        match_threshold=match_th,
        review_threshold=review_th
    )
    no_face_passed = (
        no_face_res["face_detected"] is False and
        no_face_res["recognized"] is False and
        no_face_res["attendance_marked"] is False and
        no_face_res["reason"] == "NO_FACE_DETECTED"
    )
    status_str = "PASS" if no_face_passed else "FAIL"
    if not no_face_passed: all_passed = False
    print(f"  [{status_str}] Blank Image (No Face):")
    print(f"         face_detected={no_face_res['face_detected']}, recognized={no_face_res['recognized']}, attendance_marked={no_face_res['attendance_marked']}, reason={no_face_res['reason']}")

    # Clean up test session
    db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    db.close()

    print("\n" + "=" * 60)
    print(f"OVERALL VALIDATION RESULT: {'ALL PASS' if all_passed else 'SOME FAILED'}")
    print("=" * 60)

if __name__ == "__main__":
    run_validation()
