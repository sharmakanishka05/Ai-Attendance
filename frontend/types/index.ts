export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'teacher';
  is_active: boolean;
}

export interface Student {
  id: string;
  name: string;
  roll_number: string;
  email?: string;
  class_name: string;
  section: string;
  status: string;
  has_face_data: boolean;
  face_quality_score?: number | null;
  attendance_rate: number;
  created_at: string;
}

export interface EnrollmentImageInfo {
  id: string;
  label: string;
  thumbnail_base64?: string;
  quality_score?: number;
  is_primary?: boolean;
  model_name?: string;
  model_version?: string;
  created_at?: string;
}

export interface StudentDetail extends Student {
  embeddings_count: number;
  biometric_model?: string;
  embedding_dimension?: number;
  biometric_status?: string;
  enrollment_images?: EnrollmentImageInfo[];
  stats: {
    present: number;
    late: number;
    absent: number;
    total: number;
    rate: number;
  };
  history: Array<{
    id: string;
    session_title: string;
    date: string;
    status: 'present' | 'absent' | 'late';
    confidence: number;
    marked_method: string;
    marked_at: string;
  }>;
}

export interface ClassModel {
  id: string;
  name: string;
  course: string;
  section: string;
  teacher_name: string;
  schedule?: string;
  student_count: number;
  created_at: string;
}

export interface BoundingBox {
  x: number; // percentage (0-100)
  y: number; // percentage (0-100)
  width: number; // percentage (0-100)
  height: number; // percentage (0-100)
}

export interface DetectedFace {
  box_id: string;
  bbox: BoundingBox;
  student_id?: string | null;
  student_name?: string | null;
  roll_number?: string | null;
  confidence: number;
  status: 'recognized' | 'review' | 'unknown';
  face_crop_base64?: string;
}

export interface ProcessImageResult {
  total_detected: number;
  recognized_count: number;
  review_count: number;
  unknown_count: number;
  faces: DetectedFace[];
  processed_image_data?: string;
}

export interface LiveFaceResult {
  box_id: string;
  bbox: BoundingBox;
  student_id?: string | null;
  student_name?: string | null;
  roll_number?: string | null;
  confidence: number;
  status: 'recognized' | 'review' | 'unknown';
  attendance_marked: boolean;
  attendance_status?: string;
  reason?: string | null;
  record_id?: string | null;
  face_crop_base64?: string;
}

export interface RecognizeAndMarkResult {
  face_detected: boolean;
  recognized: boolean;
  student_id?: string | null;
  student_name?: string | null;
  confidence: number;
  match_threshold: number;
  attendance_marked: boolean;
  reason?: string | null;
  session_id?: string | null;
  record_id?: string | null;
  timestamp?: string;
  total_detected?: number;
  faces?: LiveFaceResult[];
}

export interface AttendanceItem {
  student_id: string;
  student_name: string;
  roll_number: string;
  status: 'present' | 'absent' | 'late';
  confidence: number;
  marked_method: string;
  is_modified?: boolean;
  correction_reason?: string;
  face_crop_base64?: string;
}

export interface AttendanceSession {
  id: string;
  class_id: string;
  class_name?: string;
  date: string;
  time: string;
  title: string;
  status: 'active' | 'completed' | 'cancelled';
  present_count: number;
  absent_count: number;
  late_count: number;
  total_students: number;
  created_at: string;
}

export interface AttendanceReportSummary {
  attendance_rate: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  total_records: number;
  classes_today: number;
  trend: Array<{
    date: string;
    label: string;
    rate: number;
    present: number;
    absent: number;
  }>;
  class_comparisons: Array<{
    class_id: string;
    name: string;
    student_count: number;
    attendance_rate: number;
  }>;
}

export interface AuditLogItem {
  id: string;
  user_name?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details?: string;
  timestamp: string;
}

export interface QualityFeedback {
  overall_pass: boolean;
  score: number;
  feedback: string[];
  checks: {
    good_lighting: boolean;
    clearly_visible: boolean;
    face_centered: boolean;
    sharpness: boolean;
  };
}
