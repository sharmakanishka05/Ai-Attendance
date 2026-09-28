import cv2
import json
import base64
import numpy as np
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Student, FaceEmbedding, ClassModel, AttendanceSession, AttendanceRecord, SystemSetting, User
from app.schemas import (
    ProcessImageResponse, ConfirmAttendanceRequest, AttendanceCorrectionRequest, AttendanceRecordResponse,
    RecognizeAndMarkResponse
)
from app.api.auth import require_teacher_or_admin
from app.services.face_pipeline import face_pipeline
from app.services.attendance_svc import AttendanceService
from app.config import settings

router = APIRouter(prefix="/attendance", tags=["attendance"])

def get_effective_thresholds(db: Session) -> tuple[float, float]:
    """Retrieves dynamically persisted thresholds from system_settings, falling back to config"""
    m_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
    r_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
    match_th = float(m_setting.value) if m_setting else settings.FACE_MATCH_THRESHOLD
    review_th = float(r_setting.value) if r_setting else settings.FACE_REVIEW_THRESHOLD
    return match_th, review_th

@router.post("/process-image", response_model=ProcessImageResponse)
async def process_attendance_image(
    class_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    match_threshold: Optional[float] = Form(None),
    review_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    """
    Core Computer Vision endpoint:
    Processes single camera capture or large group/classroom photograph (1 to 40+ faces).
    Detects faces, generates 512-d ArcFace embeddings, runs cosine similarity matching,
    and classifies into Recognized, Review, or Unknown.
    """
    # 1. Read input image bytes
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
        raise HTTPException(
            status_code=400,
            detail="We couldn't process this image. Please provide a valid photo file or camera frame."
        )

    if img_bgr is None or img_bgr.size == 0:
        raise HTTPException(
            status_code=400,
            detail="We couldn't process this image. Make sure the photo contains clear, visible faces and try again."
        )

    # 2. Gather enrolled students' face embeddings
    if class_id:
        classroom = db.query(ClassModel).filter(ClassModel.id == class_id).first()
        target_students = classroom.students if classroom else db.query(Student).all()
    else:
        target_students = db.query(Student).all()

    enrolled_embeddings = []
    for s in target_students:
        for emb in s.face_embeddings:
            vec = emb.get_vector()
            if vec:
                enrolled_embeddings.append({
                    "student_id": s.id,
                    "student_name": s.name,
                    "roll_number": s.roll_number,
                    "vector": vec
                })

    # Retrieve dynamically persisted thresholds if not explicitly passed
    db_match_th, db_review_th = get_effective_thresholds(db)
    effective_match = match_threshold if match_threshold is not None else db_match_th
    effective_review = review_threshold if review_threshold is not None else db_review_th

    # 3. Execute Face Recognition Pipeline
    result = face_pipeline.recognize_faces(
        image_bgr=img_bgr,
        enrolled_embeddings=enrolled_embeddings,
        match_threshold=effective_match,
        review_threshold=effective_review
    )

    # Convert compressed image for display preview if needed
    h_img, w_img = img_bgr.shape[:2]
    max_dim = max(h_img, w_img)
    if max_dim > 1000:
        scale = 1000.0 / max_dim
        display_img = cv2.resize(img_bgr, (int(w_img * scale), int(h_img * scale)))
    else:
        display_img = img_bgr

    _, buffer = cv2.imencode(".jpg", display_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    img_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")
    result["processed_image_data"] = img_b64

    return result

@router.post("/confirm")
def confirm_attendance(
    payload: ConfirmAttendanceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    """
    Confirms reviewed attendance.
    Enforces duplicate prevention and commits records to database.
    """
    try:
        res = AttendanceService.confirm_session_attendance(
            db=db,
            session_id=payload.session_id,
            records_data=[item.model_dump() for item in payload.items],
            user_id=user.id,
            notes=payload.notes
        )
        return {
            "success": True,
            "message": "Attendance confirmed and saved successfully.",
            "data": res
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/correct")
def correct_attendance_record(
    payload: AttendanceCorrectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    """
    Allows teacher to manually correct attendance status.
    Mandatory reason is recorded in audit logs.
    """
    try:
        updated_record = AttendanceService.record_manual_correction(
            db=db,
            record_id=payload.record_id,
            new_status=payload.new_status,
            reason=payload.reason,
            user_id=user.id
        )
        return {
            "success": True,
            "message": f"Status updated to {updated_record.status}.",
            "record_id": updated_record.id,
            "new_status": updated_record.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recognize-and-mark", response_model=RecognizeAndMarkResponse)
async def recognize_and_mark(
    session_id: Optional[str] = Form(None),
    class_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    match_threshold: Optional[float] = Form(None),
    review_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    """
    Real-time face recognition and single-face attendance marking.
    Detects face, extracts embedding, matches against enrolled students,
    enforces duplicate attendance protection, and records structured audit log.
    """
    img_bgr = None
    if file:
        content = await file.read()
        np_arr = np.frombuffer(content, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    elif image_base64:
        header, encoded = image_base64.split(",", 1) if "," in image_base64 else ("", image_base64)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    res = AttendanceService.recognize_and_mark_attendance(
        db=db,
        image_bgr=img_bgr,
        session_id=session_id,
        class_id=class_id,
        match_threshold=match_threshold,
        review_threshold=review_threshold,
        user_id=user.id
    )
    return res
