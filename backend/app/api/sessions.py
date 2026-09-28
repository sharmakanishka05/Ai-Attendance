from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import AttendanceSession, ClassModel, AttendanceRecord, User
from app.schemas import SessionCreate, SessionResponse
from app.api.auth import require_teacher_or_admin
from app.services.attendance_svc import AttendanceService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("", response_model=List[SessionResponse])
def get_sessions(
    class_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    query = db.query(AttendanceSession)
    if class_id:
        query = query.filter(AttendanceSession.class_id == class_id)
    if status_filter:
        query = query.filter(AttendanceSession.status == status_filter)

    sessions = query.order_by(AttendanceSession.created_at.desc()).all()
    results = []
    for s in sessions:
        present_cnt = sum(1 for r in s.records if r.status == "present")
        late_cnt = sum(1 for r in s.records if r.status == "late")
        absent_cnt = sum(1 for r in s.records if r.status == "absent")
        total_students = len(s.classroom.students) if s.classroom else len(s.records)

        results.append({
            "id": s.id,
            "class_id": s.class_id,
            "class_name": s.classroom.name if s.classroom else "Class",
            "date": s.date,
            "time": s.time,
            "title": s.title,
            "status": s.status,
            "present_count": present_cnt,
            "absent_count": absent_cnt,
            "late_count": late_cnt,
            "total_students": total_students,
            "created_at": s.created_at
        })
    return results

@router.post("", response_model=SessionResponse)
def create_session(
    session_in: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    classroom = db.query(ClassModel).filter(ClassModel.id == session_in.class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")

    new_session = AttendanceService.get_or_create_session(
        db=db,
        class_id=session_in.class_id,
        date_str=session_in.date,
        time_str=session_in.time,
        title=session_in.title,
        user_id=user.id
    )

    return {
        "id": new_session.id,
        "class_id": new_session.class_id,
        "class_name": classroom.name,
        "date": new_session.date,
        "time": new_session.time,
        "title": new_session.title,
        "status": new_session.status,
        "present_count": 0,
        "absent_count": 0,
        "late_count": 0,
        "total_students": len(classroom.students),
        "created_at": new_session.created_at
    }

@router.get("/{id}")
def get_session_detail(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    session_obj = db.query(AttendanceSession).filter(AttendanceSession.id == id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    records_list = []
    for r in session_obj.records:
        records_list.append({
            "record_id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.name if r.student else "Unknown",
            "roll_number": r.student.roll_number if r.student else "",
            "status": r.status,
            "confidence": round(r.confidence, 3),
            "marked_method": r.marked_method,
            "marked_at": r.marked_at,
            "corrections": [
                {
                    "old_status": c.old_status,
                    "new_status": c.new_status,
                    "reason": c.reason,
                    "timestamp": c.timestamp
                }
                for c in r.corrections
            ]
        })

    return {
        "id": session_obj.id,
        "class_id": session_obj.class_id,
        "class_name": session_obj.classroom.name if session_obj.classroom else "Class",
        "date": session_obj.date,
        "time": session_obj.time,
        "title": session_obj.title,
        "status": session_obj.status,
        "created_at": session_obj.created_at,
        "records": records_list
    }
