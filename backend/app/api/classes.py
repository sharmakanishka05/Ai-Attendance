from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import ClassModel, Student, AuditLog, User
from app.schemas import ClassCreate, ClassResponse
from app.api.auth import require_admin, require_teacher_or_admin

router = APIRouter(prefix="/classes", tags=["classes"])

@router.get("", response_model=List[ClassResponse])
def get_classes(
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    query = db.query(ClassModel)
    if user.role == "teacher":
        query = query.filter((ClassModel.teacher_id == user.id) | (ClassModel.teacher_name == user.full_name))
    classes = query.all()
    results = []
    for c in classes:
        results.append({
            "id": c.id,
            "name": c.name,
            "course": c.course,
            "section": c.section,
            "teacher_id": c.teacher_id,
            "teacher_name": c.teacher_name,
            "schedule": c.schedule,
            "student_count": len(c.students),
            "created_at": c.created_at
        })
    return results

@router.post("", response_model=ClassResponse)
def create_class(
    class_in: ClassCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    new_class = ClassModel(
        name=class_in.name,
        course=class_in.course,
        section=class_in.section,
        teacher_id=class_in.teacher_id or user.id,
        teacher_name=class_in.teacher_name or user.full_name,
        schedule=class_in.schedule
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    audit = AuditLog(
        user_id=user.id,
        action="CLASS_CREATED",
        entity_type="ClassModel",
        entity_id=new_class.id,
        details=f"Created class {new_class.name} - {new_class.section}"
    )
    db.add(audit)
    db.commit()

    return {
        "id": new_class.id,
        "name": new_class.name,
        "course": new_class.course,
        "section": new_class.section,
        "teacher_id": new_class.teacher_id,
        "teacher_name": new_class.teacher_name,
        "schedule": new_class.schedule,
        "student_count": 0,
        "created_at": new_class.created_at
    }

@router.get("/{id}")
def get_class_detail(
    id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin)
):
    c = db.query(ClassModel).filter(ClassModel.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Class not found")

    students_data = []
    for s in c.students:
        students_data.append({
            "id": s.id,
            "name": s.name,
            "roll_number": s.roll_number,
            "has_face_data": len(s.face_embeddings) > 0,
            "status": s.status
        })

    return {
        "id": c.id,
        "name": c.name,
        "course": c.course,
        "section": c.section,
        "teacher_id": c.teacher_id,
        "teacher_name": c.teacher_name,
        "schedule": c.schedule,
        "student_count": len(c.students),
        "students": students_data,
        "created_at": c.created_at
    }
