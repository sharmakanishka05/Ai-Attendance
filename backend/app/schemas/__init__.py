from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

# --- Student Schemas ---
class StudentBase(BaseModel):
    name: str
    roll_number: str
    email: Optional[str] = None
    class_name: str
    section: str
    course: Optional[str] = None
    year: Optional[str] = None
    dataset_type: Optional[str] = "PRODUCTION"
    status: Optional[str] = "active"

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[str] = None
    email: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    course: Optional[str] = None
    year: Optional[str] = None
    dataset_type: Optional[str] = None
    status: Optional[str] = None

class StudentResponse(StudentBase):
    id: str
    has_face_data: bool = False
    face_quality_score: Optional[float] = None
    attendance_rate: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True

class RecognizeAndMarkResponse(BaseModel):
    face_detected: bool
    recognized: bool
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    confidence: float = 0.0
    match_threshold: float = 0.70
    attendance_marked: bool = False
    reason: Optional[str] = None
    session_id: Optional[str] = None
    record_id: Optional[str] = None
    timestamp: Optional[str] = None
    total_detected: Optional[int] = 0
    faces: Optional[List[Dict[str, Any]]] = None

# --- Class Schemas ---
class ClassCreate(BaseModel):
    name: str
    course: str
    section: str
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = "Ajeet Singh"
    schedule: Optional[str] = None

class ClassResponse(BaseModel):
    id: str
    name: str
    course: str
    section: str
    teacher_id: Optional[str] = None
    teacher_name: str
    schedule: Optional[str] = None
    student_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

# --- Attendance & CV Schemas ---
class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class DetectedFace(BaseModel):
    box_id: str
    bbox: BoundingBox
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    roll_number: Optional[str] = None
    confidence: float = 0.0
    status: str  # "recognized", "review", "unknown"
    face_crop_base64: Optional[str] = None

class ProcessImageResponse(BaseModel):
    total_detected: int
    recognized_count: int
    review_count: int
    unknown_count: int
    faces: List[DetectedFace]
    processed_image_data: Optional[str] = None

class AttendanceItem(BaseModel):
    student_id: str
    status: str  # "present", "absent", "late"
    confidence: float = 1.0
    marked_method: str = "ai_upload"

class ConfirmAttendanceRequest(BaseModel):
    session_id: str
    items: List[AttendanceItem]
    unknown_faces_handled: int = 0
    notes: Optional[str] = None

class AttendanceCorrectionRequest(BaseModel):
    record_id: str
    new_status: str  # "present", "absent", "late"
    reason: str

class AttendanceRecordResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    student_name: str
    roll_number: str
    status: str
    confidence: float
    marked_method: str
    marked_at: datetime

# --- Session Schemas ---
class SessionCreate(BaseModel):
    class_id: str
    date: str
    time: str
    title: str

class SessionResponse(BaseModel):
    id: str
    class_id: str
    class_name: Optional[str] = None
    date: str
    time: str
    title: str
    status: str
    present_count: int = 0
    absent_count: int = 0
    late_count: int = 0
    total_students: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

# --- Reports & Audit Schemas ---
class AttendanceReportSummary(BaseModel):
    attendance_rate: float
    present_count: int
    absent_count: int
    late_count: int
    total_records: int
    classes_today: int
    trend: List[Dict[str, Any]]
    class_comparisons: List[Dict[str, Any]]

class AuditLogResponse(BaseModel):
    id: str
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime
