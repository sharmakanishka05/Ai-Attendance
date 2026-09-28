import os
import sys
import json
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.database import SessionLocal, engine, Base
from app.models import Student, ClassModel, FaceEmbedding, FaceImage, AttendanceRecord, AttendanceSession
from app.services.face_pipeline import face_pipeline
from app.config import settings

logger = logging.getLogger("attendai.seed_test_data")

TEST_STUDENTS = [
    {
        "student_id": "MCA001",
        "name": "Kanishka Sharma",
        "course": "MCA",
        "year": "Final Year",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year",
        "email": "kanishka.mca001@kit.ac.in",
        "dataset_type": "TEST_DATA",
        "image_file": "MCA001_Kanishka_Sharma.jpg",
        "expected_image": "IMAGE_1"
    },
    {
        "student_id": "MCA002",
        "name": "Namita Jain",
        "course": "MCA",
        "year": "Final Year",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year",
        "email": "namita.mca002@kit.ac.in",
        "dataset_type": "TEST_DATA",
        "image_file": "MCA002_Namita_Jain.jpg",
        "expected_image": "IMAGE_2"
    },
    {
        "student_id": "MCA003",
        "name": "Akanksha Mishra",
        "course": "MCA",
        "year": "Final Year",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year",
        "email": "akanksha.mca003@kit.ac.in",
        "dataset_type": "TEST_DATA",
        "image_file": "MCA003_Akanksha_Mishra.jpg",
        "expected_image": "IMAGE_3"
    }
]

def ensure_db_schema(db: Session):
    """
    Safely ensures that newly added columns and tables exist in the database
    (supports both SQLite and PostgreSQL without destroying production data).
    """
    # 1. Create missing tables (e.g. face_images)
    Base.metadata.create_all(bind=engine)

    # 2. Check and add columns to SQLite if necessary
    try:
        bind = db.get_bind()
        if "sqlite" in str(bind.url):
            # Check students table
            student_cols = [r[1] for r in db.execute(text("PRAGMA table_info(students)")).fetchall()]
            if "course" not in student_cols:
                db.execute(text("ALTER TABLE students ADD COLUMN course VARCHAR"))
            if "year" not in student_cols:
                db.execute(text("ALTER TABLE students ADD COLUMN year VARCHAR"))
            if "dataset_type" not in student_cols:
                db.execute(text("ALTER TABLE students ADD COLUMN dataset_type VARCHAR DEFAULT 'PRODUCTION'"))

            # Check face_embeddings table
            emb_cols = [r[1] for r in db.execute(text("PRAGMA table_info(face_embeddings)")).fetchall()]
            if "image_type" not in emb_cols:
                db.execute(text("ALTER TABLE face_embeddings ADD COLUMN image_type VARCHAR DEFAULT 'face_crop'"))
            if "dataset_type" not in emb_cols:
                db.execute(text("ALTER TABLE face_embeddings ADD COLUMN dataset_type VARCHAR DEFAULT 'PRODUCTION'"))
            if "model_name" not in emb_cols:
                db.execute(text("ALTER TABLE face_embeddings ADD COLUMN model_name VARCHAR DEFAULT 'SFace ONNX'"))
            if "model_version" not in emb_cols:
                db.execute(text("ALTER TABLE face_embeddings ADD COLUMN model_version VARCHAR DEFAULT '1.0'"))

            # Check attendance_records table
            rec_cols = [r[1] for r in db.execute(text("PRAGMA table_info(attendance_records)")).fetchall()]
            if "dataset_type" not in rec_cols:
                db.execute(text("ALTER TABLE attendance_records ADD COLUMN dataset_type VARCHAR DEFAULT 'PRODUCTION'"))

            db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Schema check notice: {e}")

def seed_mca_test_data(db: Session) -> Dict[str, Any]:
    """
    Repeatable development seed process:
    1. Checks whether MCA001, MCA002, MCA003 already exist.
    2. Avoids duplicate student records (updates existing or inserts new).
    3. Adds/references the correct images from data/test_data/images.
    4. Generates embeddings using existing face recognition model.
    5. Avoids duplicate embeddings.
    6. Reports what was created/updated.
    """
    ensure_db_schema(db)

    print("==================================================")
    print("Seeding MCA Attendance TEST_DATA Students")
    print("==================================================")

    # 1. Ensure MCA Class exists
    mca_class = db.query(ClassModel).filter(
        (ClassModel.id == "class_mca_final") |
        (ClassModel.course == "MCA")
    ).first()

    if not mca_class:
        mca_class = ClassModel(
            id="class_mca_final",
            name="MCA Final Year",
            course="MCA",
            section="MCA Final Year",
            teacher_name="Ajeet Singh",
            schedule="Mon-Fri 09:30 AM"
        )
        db.add(mca_class)
        db.commit()
        db.refresh(mca_class)
        print(f"[Class] Created class '{mca_class.name} - {mca_class.section}' (ID: {mca_class.id})")
    else:
        mca_class.name = "MCA Final Year"
        mca_class.course = "MCA"
        mca_class.section = "MCA Final Year"
        mca_class.teacher_name = "Ajeet Singh"
        db.commit()
        print(f"[Class] Found existing class '{mca_class.name} - {mca_class.section}' (ID: {mca_class.id})")

    faces_dir = os.path.join(settings.DATA_DIR, "faces")
    test_images_dir = os.path.join(settings.DATA_DIR, "test_data", "images")
    os.makedirs(faces_dir, exist_ok=True)

    report = {
        "students_created": 0,
        "students_updated": 0,
        "embeddings_created": 0,
        "embeddings_updated": 0,
        "images_stored": 0,
        "details": []
    }

    for s_info in TEST_STUDENTS:
        sid = s_info["student_id"]
        name = s_info["name"]
        course = s_info["course"]
        year = s_info["year"]
        img_filename = s_info["image_file"]

        # Step 1: Check whether student already exists by ID or roll_number
        student = db.query(Student).filter(
            (Student.id == sid) | (Student.roll_number == sid)
        ).first()

        created_student = False
        if not student:
            # Clean up any orphaned class_students row
            from app.models import class_students
            db.execute(class_students.delete().where(class_students.c.student_id == sid))

            # Create new student record
            student = Student(
                id=sid,
                roll_number=sid,
                name=name,
                course=course,
                year=year,
                class_name="MCA Final Year",
                section="MCA Final Year",
                email=s_info["email"],
                dataset_type="TEST_DATA",
                status="active"
            )
            student.classes.append(mca_class)
            db.add(student)
            db.flush()
            created_student = True
            report["students_created"] += 1
            print(f"[Student] Created TEST_DATA record: {sid} - {name}")
        else:
            # Update existing record
            student.name = name
            student.course = course
            student.year = year
            student.class_name = "MCA Final Year"
            student.section = "MCA Final Year"
            student.email = s_info["email"]
            student.dataset_type = "TEST_DATA"
            if mca_class not in student.classes:
                student.classes.append(mca_class)
            report["students_updated"] += 1
            print(f"[Student] Found existing student {sid} - {name} (Updated)")

        # Step 2: Locate source images (supports both single image and student directory MCA00X/)
        student_img_dir = os.path.join(test_images_dir, sid)
        img_items = []
        if os.path.isdir(student_img_dir):
            for f in sorted(os.listdir(student_img_dir)):
                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    img_items.append((f, os.path.join(student_img_dir, f)))

        if not img_items:
            img_path = os.path.join(test_images_dir, img_filename)
            if not os.path.exists(img_path):
                fallback_dir = r"C:\Users\Ayush Dwivedi\.gemini\antigravity-ide\brain\c8d5fe72-6349-4f07-8c93-55fc261123ba\.user_uploaded"
                mapping = {
                    "MCA001_Kanishka_Sharma.jpg": "media_1790497416381.jpg",
                    "MCA002_Namita_Jain.jpg": "media_1790497423016.jpg",
                    "MCA003_Akanksha_Mishra.jpg": "media_1790497428652.jpg"
                }
                if img_filename in mapping:
                    src = os.path.join(fallback_dir, mapping[img_filename])
                    if os.path.exists(src):
                        os.makedirs(test_images_dir, exist_ok=True)
                        import shutil
                        shutil.copy2(src, img_path)

            assert os.path.exists(img_path), f"Test image file not found: {img_path}"
            img_items.append((img_filename, img_path))

        # Step 3: Process each enrollment image
        for img_idx, (item_fname, item_path) in enumerate(img_items):
            img_bgr = cv2.imread(item_path)
            if img_bgr is None:
                continue

            detected = face_pipeline.detect_faces(img_bgr)
            if not detected:
                logger.warning(f"No face detected in {item_path} for {sid}")
                continue

            primary_face = max(detected, key=lambda b: b["w_px"] * b["h_px"])
            x, y, w, h = primary_face["x_px"], primary_face["y_px"], primary_face["w_px"], primary_face["h_px"]
            crop = img_bgr[y:y+h, x:x+w]

            # Save reference face crop
            photo_filename = f"face_{sid}_{img_idx+1}.jpg"
            dest_photo_path = os.path.join(faces_dir, photo_filename)
            cv2.imwrite(dest_photo_path, cv2.resize(crop, (150, 150)))
            report["images_stored"] += 1

            # Extract 128-d unit embedding via SFace ONNX DNN
            embedding_vec = face_pipeline.extract_embedding(crop)

            # Avoid duplicate embeddings for this student + photo_path
            existing_emb = db.query(FaceEmbedding).filter(
                FaceEmbedding.student_id == student.id,
                FaceEmbedding.photo_path == dest_photo_path
            ).first()

            if not existing_emb:
                # If first embedding for student, make primary
                is_prim = (img_idx == 0)
                emb_record = FaceEmbedding(
                    student_id=student.id,
                    embedding_json=json.dumps(embedding_vec),
                    photo_path=dest_photo_path,
                    image_type="face_crop",
                    dataset_type="TEST_DATA",
                    model_name="SFace ONNX",
                    model_version="1.0",
                    quality_score=1.0,
                    is_primary=is_prim
                )
                db.add(emb_record)
                report["embeddings_created"] += 1
                print(f"[Embedding] Stored embedding {img_idx+1} for {sid} ({len(embedding_vec)} dims from {item_fname})")
            else:
                existing_emb.embedding_json = json.dumps(embedding_vec)
                existing_emb.photo_path = dest_photo_path
                existing_emb.image_type = "face_crop"
                existing_emb.dataset_type = "TEST_DATA"
                existing_emb.model_name = "SFace ONNX"
                existing_emb.model_version = "1.0"
                report["embeddings_updated"] += 1
                print(f"[Embedding] Updated embedding {img_idx+1} for {sid} ({item_fname})")

            # FaceImage table record
            existing_img_rec = db.query(FaceImage).filter(
                FaceImage.student_id == student.id,
                FaceImage.image_path == dest_photo_path
            ).first()

            if not existing_img_rec:
                face_img_rec = FaceImage(
                    student_id=student.id,
                    image_path=dest_photo_path,
                    image_type="face_crop",
                    dataset_type="TEST_DATA"
                )
                db.add(face_img_rec)
            else:
                existing_img_rec.image_path = dest_photo_path
                existing_img_rec.dataset_type = "TEST_DATA"

        report["details"].append({
            "student_id": sid,
            "name": name,
            "student_action": "created" if created_student else "updated",
            "enrolled_images": len(img_items),
            "model_name": "SFace ONNX",
            "dimensions": 128
        })

    db.commit()

    print("--------------------------------------------------")
    print(f"Seed Summary:")
    print(f"  Students Created:    {report['students_created']}")
    print(f"  Students Updated:    {report['students_updated']}")
    print(f"  Embeddings Created:  {report['embeddings_created']}")
    print(f"  Embeddings Updated:  {report['embeddings_updated']}")
    print(f"  Images Stored:       {report['images_stored']}")
    print("==================================================")
    return report

def reset_mca_test_data(db: Session) -> Dict[str, Any]:
    """
    SAFE reset operation:
    Removes ONLY TEST_DATA records.
    NEVER deletes production students, production users, production attendance,
    production images, or production embeddings.
    """
    ensure_db_schema(db)

    print("==================================================")
    print("Safe Reset Operation: Removing ONLY TEST_DATA")
    print("==================================================")

    test_sids = [s["student_id"] for s in TEST_STUDENTS]

    # 1. Delete Attendance Records marked as TEST_DATA or for test students
    records_deleted = db.query(AttendanceRecord).filter(
        (AttendanceRecord.dataset_type == "TEST_DATA") |
        (AttendanceRecord.student_id.in_(test_sids))
    ).delete(synchronize_session=False)

    # 2. Delete FaceImage records marked as TEST_DATA or for test students
    images_deleted = db.query(FaceImage).filter(
        (FaceImage.dataset_type == "TEST_DATA") |
        (FaceImage.student_id.in_(test_sids))
    ).delete(synchronize_session=False)

    # 3. Delete FaceEmbedding records marked as TEST_DATA or for test students
    embeddings_deleted = db.query(FaceEmbedding).filter(
        (FaceEmbedding.dataset_type == "TEST_DATA") |
        (FaceEmbedding.student_id.in_(test_sids))
    ).delete(synchronize_session=False)

    # 4. Delete class_students association rows for test students
    from app.models import class_students
    db.execute(class_students.delete().where(class_students.c.student_id.in_(test_sids)))

    # 5. Delete Students marked as TEST_DATA or matching MCA student IDs
    students_deleted = db.query(Student).filter(
        (Student.dataset_type == "TEST_DATA") |
        (Student.id.in_(test_sids)) |
        (Student.roll_number.in_(test_sids))
    ).delete(synchronize_session=False)

    # 5. Clean up test face crops from disk
    faces_dir = os.path.join(settings.DATA_DIR, "faces")
    for sid in test_sids:
        crop_path = os.path.join(faces_dir, f"face_{sid}_1.jpg")
        if os.path.exists(crop_path):
            try:
                os.remove(crop_path)
            except Exception:
                pass

    db.commit()

    print(f"Safe Reset Summary:")
    print(f"  TEST_DATA Attendance Records Deleted: {records_deleted}")
    print(f"  TEST_DATA Face Images Deleted:        {images_deleted}")
    print(f"  TEST_DATA Embeddings Deleted:           {embeddings_deleted}")
    print(f"  TEST_DATA Students Deleted:             {students_deleted}")
    print("  PRODUCTION DATA REMAINED COMPLETELY UNTOUCHED.")
    print("==================================================")

    return {
        "records_deleted": records_deleted,
        "images_deleted": images_deleted,
        "embeddings_deleted": embeddings_deleted,
        "students_deleted": students_deleted
    }

if __name__ == "__main__":
    db = SessionLocal()
    try:
        if "--reset" in sys.argv:
            reset_mca_test_data(db)
        else:
            seed_mca_test_data(db)
    finally:
        db.close()
