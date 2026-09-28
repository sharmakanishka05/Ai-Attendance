import os
import cv2
import json
import base64
import numpy as np
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Student, FaceEmbedding, AttendanceRecord, AuditLog, ClassModel, User
from app.schemas import StudentCreate, StudentUpdate, StudentResponse
from app.api.auth import require_admin, require_teacher_or_admin
from app.services.face_pipeline import face_pipeline
from app.services.quality_check import ImageQualityChecker
from app.config import settings

router = APIRouter(prefix="/students", tags=["students"])

@router.get("", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = None,
    class_name: Optional[str] = None,
    section: Optional[str] = None,
    has_face: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    query = db.query(Student)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter((Student.name.ilike(search_fmt)) | (Student.roll_number.ilike(search_fmt)))

    if class_name and class_name != "all":
        query = query.filter(Student.class_name == class_name)

    if section and section != "all":
        query = query.filter(Student.section == section)

    students = query.order_by(Student.roll_number.asc()).all()

    results = []
    for s in students:
        has_face_data = len(s.face_embeddings) > 0
        if has_face is not None and has_face != has_face_data:
            continue

        # Calculate attendance percentage
        total_records = len(s.attendance_records)
        present_count = sum(1 for r in s.attendance_records if r.status in ["present", "late"])
        attendance_rate = round((present_count / total_records * 100.0), 1) if total_records > 0 else 0.0

        best_quality = max([f.quality_score for f in s.face_embeddings], default=None)

        results.append({
            "id": s.id,
            "name": s.name,
            "roll_number": s.roll_number,
            "email": s.email,
            "class_name": s.class_name,
            "section": s.section,
            "course": getattr(s, "course", None) or s.class_name,
            "year": getattr(s, "year", None) or s.section,
            "dataset_type": getattr(s, "dataset_type", "PRODUCTION") or "PRODUCTION",
            "status": s.status,
            "has_face_data": has_face_data,
            "face_quality_score": best_quality,
            "attendance_rate": attendance_rate,
            "created_at": s.created_at
        })

    return results

@router.post("", response_model=StudentResponse)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    # Check duplicate roll number
    existing = db.query(Student).filter(Student.roll_number == student_in.roll_number).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A student with roll number '{student_in.roll_number}' already exists."
        )

    student = Student(
        name=student_in.name,
        roll_number=student_in.roll_number,
        email=student_in.email,
        class_name=student_in.class_name,
        section=student_in.section,
        course=student_in.course or student_in.class_name,
        year=student_in.year or student_in.section,
        dataset_type=student_in.dataset_type or "PRODUCTION",
        status=student_in.status or "active"
    )
    db.add(student)

    # Associate with class if exists
    classroom = db.query(ClassModel).filter(
        ClassModel.name == student_in.class_name,
        ClassModel.section == student_in.section
    ).first()
    if classroom:
        student.classes.append(classroom)

    db.commit()
    db.refresh(student)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="STUDENT_CREATED",
        entity_type="Student",
        entity_id=student.id,
        details=f"Created student {student.name} ({student.roll_number}) in {student.class_name} - {student.section}"
    )
    db.add(audit)
    db.commit()

    return {
        "id": student.id,
        "name": student.name,
        "roll_number": student.roll_number,
        "email": student.email,
        "class_name": student.class_name,
        "section": student.section,
        "course": student.course,
        "year": student.year,
        "dataset_type": student.dataset_type,
        "status": student.status,
        "has_face_data": False,
        "face_quality_score": None,
        "attendance_rate": 0.0,
        "created_at": student.created_at
    }

@router.get("/{id}")
def get_student_detail(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    records = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == id).all()
    present_cnt = sum(1 for r in records if r.status == "present")
    late_cnt = sum(1 for r in records if r.status == "late")
    absent_cnt = sum(1 for r in records if r.status == "absent")
    total = len(records)
    rate = round(((present_cnt + late_cnt) / total * 100.0), 1) if total > 0 else 0.0

    history = []
    for r in sorted(records, key=lambda x: x.marked_at, reverse=True)[:15]:
        history.append({
            "id": r.id,
            "session_title": r.session.title if r.session else "Regular Class",
            "date": r.session.date if r.session else r.marked_at.strftime("%Y-%m-%d"),
            "status": r.status,
            "confidence": round(r.confidence, 3),
            "marked_method": r.marked_method,
            "marked_at": r.marked_at
        })

    has_face = len(student.face_embeddings) > 0
    enrollment_images = []
    for idx, emb in enumerate(student.face_embeddings):
        img_item = {
            "id": emb.id,
            "label": f"Image {idx + 1}",
            "quality_score": round(emb.quality_score or 1.0, 2),
            "is_primary": emb.is_primary,
            "model_name": emb.model_name or "SFace",
            "model_version": emb.model_version or "1.0",
            "created_at": emb.created_at.isoformat() if hasattr(emb.created_at, "isoformat") else str(emb.created_at)
        }
        if emb.photo_path and os.path.exists(emb.photo_path):
            try:
                with open(emb.photo_path, "rb") as pf:
                    b64 = base64.b64encode(pf.read()).decode("utf-8")
                    img_item["thumbnail_base64"] = f"data:image/jpeg;base64,{b64}"
            except Exception:
                pass
        enrollment_images.append(img_item)

    return {
        "id": student.id,
        "name": student.name,
        "roll_number": student.roll_number,
        "email": student.email,
        "class_name": student.class_name,
        "section": student.section,
        "course": getattr(student, "course", None) or student.class_name,
        "year": getattr(student, "year", None) or student.section,
        "dataset_type": getattr(student, "dataset_type", "PRODUCTION") or "PRODUCTION",
        "status": student.status,
        "has_face_data": has_face,
        "embeddings_count": len(student.face_embeddings),
        "biometric_model": "SFace",
        "embedding_dimension": 128,
        "biometric_status": "ENROLLED" if has_face else "NOT ENROLLED",
        "enrollment_images": enrollment_images,
        "created_at": student.created_at,
        "stats": {
            "present": present_cnt,
            "late": late_cnt,
            "absent": absent_cnt,
            "total": total,
            "rate": rate
        },
        "history": history
    }

@router.post("/{id}/face-registration")
async def register_student_face(
    id: str,
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Read image bytes
    if file:
        content = await file.read()
        np_arr = np.frombuffer(content, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    elif image_base64:
        header, encoded = image_base64.split(",", 1) if "," in image_base64 else ("", image_base64)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    else:
        raise HTTPException(status_code=400, detail="No image file or base64 data provided.")

    if img_bgr is None or img_bgr.size == 0:
        raise HTTPException(status_code=400, detail="Invalid image format.")

    # 1. Detect face in the registration image
    detected = face_pipeline.detect_faces(img_bgr)
    if not detected:
        quality_feedback = ImageQualityChecker.evaluate_face_image(img_bgr)
        return {
            "success": False,
            "message": "No face detected in the photo. Please center your face under good lighting.",
            "quality": quality_feedback
        }

    # Use the primary/largest face
    primary_face = max(detected, key=lambda d: d["w_px"] * d["h_px"])
    bbox = (primary_face["x_px"], primary_face["y_px"], primary_face["w_px"], primary_face["h_px"])

    # 2. Quality Evaluation
    quality = ImageQualityChecker.evaluate_face_image(img_bgr, bbox)

    # 3. Crop face & extract 512-d ArcFace embedding
    x, y, w, h = bbox
    face_crop = img_bgr[y:y+h, x:x+w]
    embedding_vec = face_pipeline.extract_embedding(face_crop)

    # Save reference thumbnail securely in DATA_DIR
    photo_filename = f"face_{student.id}_{len(student.face_embeddings)+1}.jpg"
    photo_path = os.path.join(settings.DATA_DIR, "faces", photo_filename)
    cv2.imwrite(photo_path, cv2.resize(face_crop, (150, 150)))

    # Store embedding record
    new_embedding = FaceEmbedding(
        student_id=student.id,
        embedding_json=json.dumps(embedding_vec),
        photo_path=photo_path,
        quality_score=quality["score"],
        is_primary=True
    )
    db.add(new_embedding)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="FACE_REGISTERED",
        entity_type="Student",
        entity_id=student.id,
        details=f"Registered biometric face reference for {student.name}. Quality score: {quality['score']}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Face registered successfully!",
        "quality": quality,
        "total_embeddings": len(student.face_embeddings)
    }

@router.delete("/{id}/face-data")
def delete_student_face_data(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    """
    Privacy / GDPR compliance: Purges student biometric face data without wiping historical attendance records.
    Restricted to Administrators only.
    """
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    count = len(student.face_embeddings)
    for emb in student.face_embeddings:
        if emb.photo_path and os.path.exists(emb.photo_path):
            try:
                os.remove(emb.photo_path)
            except Exception:
                pass
        db.delete(emb)

    audit = AuditLog(
        user_id=user.id,
        action="BIOMETRIC_DATA_PURGED",
        entity_type="Student",
        entity_id=student.id,
        details=f"Permanently purged {count} biometric face embeddings for student {student.name} ({student.roll_number})"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully deleted {count} face biometric records for {student.name}."
    }

@router.delete("/{id}")
def delete_student(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    name = student.name
    roll = student.roll_number
    db.delete(student)
    audit = AuditLog(
        user_id=user.id,
        action="STUDENT_DELETED",
        entity_type="Student",
        entity_id=id,
        details=f"Deleted student record for {name} ({roll})"
    )
    db.add(audit)
    db.commit()
    return {"success": True, "message": f"Student {name} deleted successfully."}
