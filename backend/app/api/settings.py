import os
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import SystemSetting, AuditLog, User
from app.api.auth import require_admin, require_teacher_or_admin
from app.config import settings
from app.services.face_pipeline import face_pipeline

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdateSchema(BaseModel):
    face_match_threshold: Optional[float] = Field(None, ge=0.40, le=0.99)
    face_review_threshold: Optional[float] = Field(None, ge=0.30, le=0.90)

@router.get("")
def get_system_settings(
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
) -> Dict[str, Any]:
    """
    Returns current recognition thresholds and system diagnostics.
    """
    m_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
    r_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()

    match_th = float(m_setting.value) if m_setting else settings.FACE_MATCH_THRESHOLD
    review_th = float(r_setting.value) if r_setting else settings.FACE_REVIEW_THRESHOLD

    # Determine internal diagnostics
    yunet_ready = getattr(face_pipeline, "yunet_detector", None) is not None
    cascade_ready = getattr(face_pipeline, "cascade", None) is not None
    sface_ready = getattr(face_pipeline, "sface_recognizer", None) is not None
    arcface_ready = getattr(face_pipeline, "embedding_session", None) is not None
    deep_model_ready = sface_ready or arcface_ready

    detector_desc = "READY (YuNet DNN)" if yunet_ready else ("READY (Haar Cascade Fallback)" if cascade_ready else "UNAVAILABLE")
    if sface_ready:
        embedding_desc = "READY (SFace ONNX DNN)"
    elif arcface_ready:
        embedding_desc = "READY (ArcFace ONNX)"
    else:
        embedding_desc = "READY (512-d Spatial Feature Fallback)"

    recognition_mode = "REAL MODEL" if deep_model_ready else "FALLBACK"

    return {
        "face_match_threshold": match_th,
        "face_review_threshold": review_th,
        "app_env": settings.APP_ENV,
        "diagnostics": {
            "face_detector": detector_desc,
            "embedding_model": embedding_desc,
            "recognition_mode": recognition_mode,
            "models_dir": os.path.abspath(settings.MODELS_DIR),
            "onnx_model_file_present": deep_model_ready
        }
    }

@router.put("")
def update_system_settings(
    payload: SettingsUpdateSchema,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    """
    Allows authorized administrators to persist threshold changes in the database.
    """
    updated_items = []

    if payload.face_match_threshold is not None:
        m = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
        if not m:
            m = SystemSetting(key="FACE_MATCH_THRESHOLD", value=str(payload.face_match_threshold), description="Face Match Threshold", updated_by_id=user.id)
            db.add(m)
        else:
            m.value = str(payload.face_match_threshold)
            m.updated_by_id = user.id
            m.updated_at = datetime.utcnow()
        updated_items.append(f"FACE_MATCH_THRESHOLD={payload.face_match_threshold}")

    if payload.face_review_threshold is not None:
        r = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
        if not r:
            r = SystemSetting(key="FACE_REVIEW_THRESHOLD", value=str(payload.face_review_threshold), description="Face Review Threshold", updated_by_id=user.id)
            db.add(r)
        else:
            r.value = str(payload.face_review_threshold)
            r.updated_by_id = user.id
            r.updated_at = datetime.utcnow()
        updated_items.append(f"FACE_REVIEW_THRESHOLD={payload.face_review_threshold}")

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="SETTINGS_UPDATED",
        entity_type="SystemSetting",
        entity_id=None,
        details=f"Admin {user.full_name} updated recognition thresholds: {', '.join(updated_items)}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "System settings persisted to database successfully.",
        "updated": updated_items
    }
