from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrection, AuditLog, Student, ClassModel
)

class AttendanceService:
    @staticmethod
    def get_or_create_session(
        db: Session,
        class_id: str,
        date_str: str,
        time_str: str,
        title: str,
        user_id: Optional[str] = None
    ) -> AttendanceSession:
        """Retrieves existing active session or creates a new attendance session"""
        existing = db.query(AttendanceSession).filter(
            AttendanceSession.class_id == class_id,
            AttendanceSession.date == date_str,
            AttendanceSession.status == "active"
        ).first()

        if existing:
            return existing

        new_session = AttendanceSession(
            class_id=class_id,
            date=date_str,
            time=time_str,
            title=title,
            status="active",
            created_by=user_id
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        # Audit log for session creation
        audit = AuditLog(
            user_id=user_id,
            action="SESSION_CREATED",
            entity_type="AttendanceSession",
            entity_id=new_session.id,
            details=f"Created session '{title}' for class {class_id} on {date_str} {time_str}"
        )
        db.add(audit)
        db.commit()

        return new_session

    @staticmethod
    def confirm_session_attendance(
        db: Session,
        session_id: str,
        records_data: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Commits final reviewed attendance to database.
        Strictly prevents duplicate attendance records for the same student in the same session.
        """
        session_obj = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
        if not session_obj:
            raise ValueError("Session not found")

        saved_records = []
        present_count = 0
        absent_count = 0
        late_count = 0

        # Retrieve enrolled students for this class to identify absent students
        classroom = db.query(ClassModel).filter(ClassModel.id == session_obj.class_id).first()
        enrolled_student_ids = {s.id for s in classroom.students} if classroom and classroom.students else set()

        processed_student_ids = set()

        for item in records_data:
            s_id = item["student_id"]
            if s_id in processed_student_ids:
                # Prevent duplicate entry in the same submission batch
                continue
            processed_student_ids.add(s_id)

            status = item.get("status", "present").lower()
            confidence = float(item.get("confidence", 1.0))
            marked_method = item.get("marked_method", "ai_upload")

            # Check if record already exists for this (session_id, student_id)
            rec = db.query(AttendanceRecord).filter(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.student_id == s_id
            ).first()

            if rec:
                # Update existing record
                rec.status = status
                rec.confidence = confidence
                rec.marked_method = marked_method
                rec.marked_at = datetime.utcnow()
            else:
                rec = AttendanceRecord(
                    session_id=session_id,
                    student_id=s_id,
                    status=status,
                    confidence=confidence,
                    marked_method=marked_method
                )
                db.add(rec)

            if status == "present":
                present_count += 1
            elif status == "absent":
                absent_count += 1
            elif status == "late":
                late_count += 1

            saved_records.append(rec)

        # For any enrolled students not in the processed list, automatically mark as absent
        for s_id in enrolled_student_ids - processed_student_ids:
            rec = db.query(AttendanceRecord).filter(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.student_id == s_id
            ).first()
            if not rec:
                rec = AttendanceRecord(
                    session_id=session_id,
                    student_id=s_id,
                    status="absent",
                    confidence=1.0,
                    marked_method="manual"
                )
                db.add(rec)
                absent_count += 1
                saved_records.append(rec)

        # Mark session as completed
        session_obj.status = "completed"
        try:
            db.commit()
        except Exception:
            db.rollback()
            session_obj = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
            if session_obj and session_obj.status == "completed":
                saved_records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()
                return {
                    "session_id": session_id,
                    "status": "completed",
                    "present_count": sum(1 for r in saved_records if r.status == "present"),
                    "late_count": sum(1 for r in saved_records if r.status == "late"),
                    "absent_count": sum(1 for r in saved_records if r.status == "absent"),
                    "total_marked": len(saved_records)
                }
            raise

        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action="ATTENDANCE_CONFIRMED",
            entity_type="AttendanceSession",
            entity_id=session_id,
            details=f"Confirmed attendance: {present_count} Present, {late_count} Late, {absent_count} Absent. Notes: {notes or 'None'}"
        )
        db.add(audit)
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            "session_id": session_id,
            "status": "completed",
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "total_marked": len(saved_records)
        }

    @staticmethod
    def recognize_and_mark_attendance(
        db: Session,
        image_bgr: Any,
        session_id: Optional[str] = None,
        class_id: Optional[str] = None,
        match_threshold: Optional[float] = None,
        review_threshold: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes single camera frame or uploaded image:
        1. Detects face in image.
        2. If no face detected -> returns face_detected=False, recognized=False, attendance_marked=False, reason="NO_FACE_DETECTED"
        3. If face detected -> extracts embedding using existing model.
        4. Matches against enrolled students using existing cosine similarity.
        5. If similarity < threshold -> returns recognized=False, student_id=None, attendance_marked=False, reason="UNKNOWN_PERSON"
        6. If similarity >= threshold -> checks duplicate attendance for this session.
           - If already marked -> attendance_marked=False, reason="ALREADY_MARKED"
           - If not marked -> creates AttendanceRecord, attendance_marked=True, reason=None
        7. Logs structured development event matching specification.
        """
        import logging
        from app.config import settings
        from app.models import SystemSetting
        from app.services.face_pipeline import face_pipeline

        logger = logging.getLogger("attendai.attendance")

        # 1. Effective thresholds
        m_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
        r_setting = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
        eff_match = match_threshold if match_threshold is not None else (float(m_setting.value) if m_setting else settings.FACE_MATCH_THRESHOLD)
        eff_review = review_threshold if review_threshold is not None else (float(r_setting.value) if r_setting else settings.FACE_REVIEW_THRESHOLD)

        # 2. Ensure an active session exists
        if not session_id:
            active_query = db.query(AttendanceSession).filter(AttendanceSession.status == "active")
            if class_id:
                active_query = active_query.filter(AttendanceSession.class_id == class_id)
            active_session = active_query.first()

            if not active_session:
                # Create a session for today
                target_class = None
                if class_id:
                    target_class = db.query(ClassModel).filter(ClassModel.id == class_id).first()
                if not target_class:
                    target_class = db.query(ClassModel).first()

                today_str = datetime.utcnow().strftime("%Y-%m-%d")
                class_fk = target_class.id if target_class else "default_class"
                active_session = AttendanceSession(
                    class_id=class_fk,
                    date=today_str,
                    time=datetime.utcnow().strftime("%I:%M %p"),
                    title=f"Attendance Session - {today_str}",
                    status="active",
                    created_by=user_id
                )
                db.add(active_session)
                db.commit()
                db.refresh(active_session)
            session_id = active_session.id

        timestamp = datetime.utcnow().isoformat()

        # 3. Detect face
        if image_bgr is None or (hasattr(image_bgr, "size") and image_bgr.size == 0):
            res = {
                "timestamp": timestamp,
                "face_detected": False,
                "recognized": False,
                "student_id": None,
                "student_name": None,
                "confidence": 0.0,
                "match_threshold": eff_match,
                "attendance_marked": False,
                "reason": "NO_FACE_DETECTED",
                "session_id": session_id,
                "record_id": None
            }
            logger.info(
                f"[ATTENDANCE_CV_EVENT] timestamp={timestamp} | student_id=None | "
                f"face_detected=False | recognized=False | confidence=0.000 | "
                f"threshold={eff_match:.2f} | attendance_marked=False | reason=NO_FACE_DETECTED"
            )
            return res

        detected_boxes = face_pipeline.detect_faces(image_bgr)
        if not detected_boxes:
            res = {
                "timestamp": timestamp,
                "face_detected": False,
                "recognized": False,
                "student_id": None,
                "student_name": None,
                "confidence": 0.0,
                "match_threshold": eff_match,
                "attendance_marked": False,
                "reason": "NO_FACE_DETECTED",
                "session_id": session_id,
                "record_id": None,
                "total_detected": 0,
                "faces": []
            }
            logger.info(
                f"[ATTENDANCE_CV_EVENT] timestamp={timestamp} | student_id=None | "
                f"face_detected=False | recognized=False | confidence=0.000 | "
                f"threshold={eff_match:.2f} | attendance_marked=False | reason=NO_FACE_DETECTED"
            )
            return res

        # 4. Compare with enrolled students for each detected face independently
        all_students = db.query(Student).all()
        faces_results = []
        any_attendance_marked = False

        for box in detected_boxes:
            x, y, w, h = box["x_px"], box["y_px"], box["w_px"], box["h_px"]
            crop = image_bgr[y:y+h, x:x+w]
            
            # Generate thumbnail for review
            crop_b64 = None
            try:
                crop_thumb = cv2.resize(crop, (96, 96))
                _, t_buf = cv2.imencode(".jpg", crop_thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                import base64
                crop_b64 = "data:image/jpeg;base64," + base64.b64encode(t_buf).decode("utf-8")
            except Exception:
                pass

            query_vec = face_pipeline.extract_embedding(crop)

            best_match = None
            best_score = 0.0

            for s in all_students:
                for emb in s.face_embeddings:
                    s_vec = emb.get_vector()
                    if s_vec:
                        score = face_pipeline.cosine_similarity(query_vec, s_vec)
                        if score > best_score:
                            best_score = score
                            best_match = s

            conf = round(float(best_score), 3)

            # Evaluate thresholds
            if best_match is not None and best_score >= eff_match:
                status = "recognized"
                s_id = best_match.id
                s_name = best_match.name
                s_roll = best_match.roll_number

                # Check duplicate attendance in current session
                existing_record = db.query(AttendanceRecord).filter(
                    AttendanceRecord.session_id == session_id,
                    AttendanceRecord.student_id == s_id
                ).first()

                if existing_record:
                    face_marked = False
                    face_reason = "ALREADY_MARKED"
                    rec_id = existing_record.id
                    att_status = "ALREADY_MARKED"
                else:
                    new_rec = AttendanceRecord(
                        session_id=session_id,
                        student_id=s_id,
                        status="present",
                        confidence=conf,
                        marked_method="ai_camera",
                        dataset_type=getattr(best_match, "dataset_type", "PRODUCTION") or "PRODUCTION"
                    )
                    db.add(new_rec)
                    db.flush()
                    face_marked = True
                    any_attendance_marked = True
                    face_reason = None
                    rec_id = new_rec.id
                    att_status = "PRESENT"

            elif best_match is not None and best_score >= eff_review:
                status = "review"
                s_id = best_match.id
                s_name = best_match.name
                s_roll = best_match.roll_number
                face_marked = False
                face_reason = "REVIEW_REQUIRED"
                rec_id = None
                att_status = "REVIEW_REQUIRED"
            else:
                status = "unknown"
                s_id = None
                s_name = None
                s_roll = None
                face_marked = False
                face_reason = "UNKNOWN_PERSON"
                rec_id = None
                att_status = "NO ATTENDANCE"

            face_dict = {
                "box_id": box["box_id"],
                "bbox": box["bbox"],
                "student_id": s_id,
                "student_name": s_name,
                "roll_number": s_roll,
                "confidence": conf,
                "status": status,
                "attendance_marked": face_marked,
                "attendance_status": att_status,
                "reason": face_reason,
                "record_id": rec_id,
                "face_crop_base64": crop_b64
            }
            faces_results.append(face_dict)

            # Audit log per face (strictly no raw biometric embeddings in log)
            logger.info(
                f"[ATTENDANCE_CV_EVENT] timestamp={timestamp} | student_id={s_id} | "
                f"face_detected=True | recognized={status == 'recognized'} | confidence={conf:.3f} | "
                f"threshold={eff_match:.2f} | attendance_marked={face_marked} | reason={face_reason or 'SUCCESS'}"
            )
            audit = AuditLog(
                user_id=user_id,
                action="RECOGNITION_EVENT",
                entity_type="AttendanceSession",
                entity_id=session_id,
                details=(
                    f"timestamp={timestamp} | student_id={s_id} | face_detected=True | "
                    f"recognized={status == 'recognized'} | confidence={conf:.3f} | "
                    f"threshold={eff_match:.2f} | attendance_marked={face_marked} | reason={face_reason or 'SUCCESS'}"
                )
            )
            db.add(audit)

        db.commit()

        # Determine primary face for top-level summary backward compatibility
        recognized_faces = [f for f in faces_results if f["status"] == "recognized"]
        if recognized_faces:
            primary = max(recognized_faces, key=lambda f: f["confidence"])
            res = {
                "timestamp": timestamp,
                "face_detected": True,
                "recognized": True,
                "student_id": primary["student_id"],
                "student_name": primary["student_name"],
                "confidence": primary["confidence"],
                "match_threshold": eff_match,
                "attendance_marked": primary["attendance_marked"],
                "reason": primary["reason"],
                "session_id": session_id,
                "record_id": primary["record_id"],
                "total_detected": len(faces_results),
                "faces": faces_results
            }
        else:
            primary = max(faces_results, key=lambda f: f["confidence"])
            res = {
                "timestamp": timestamp,
                "face_detected": True,
                "recognized": False,
                "student_id": None,
                "student_name": None,
                "confidence": primary["confidence"],
                "match_threshold": eff_match,
                "attendance_marked": False,
                "reason": primary["reason"] or "UNKNOWN_PERSON",
                "session_id": session_id,
                "record_id": None,
                "total_detected": len(faces_results),
                "faces": faces_results
            }

        return res

    @staticmethod
    def record_manual_correction(
        db: Session,
        record_id: str,
        new_status: str,
        reason: str,
        user_id: Optional[str] = None
    ) -> AttendanceRecord:
        """
        Records a manual correction to an attendance record with mandatory audit trail reason.
        """
        record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
        if not record:
            raise ValueError("Attendance record not found")

        old_status = record.status
        record.status = new_status
        record.marked_method = "manual"

        # Create correction audit log
        correction = AttendanceCorrection(
            record_id=record_id,
            changed_by_user_id=user_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason
        )
        db.add(correction)

        audit = AuditLog(
            user_id=user_id,
            action="MANUAL_CORRECTION",
            entity_type="AttendanceRecord",
            entity_id=record_id,
            details=f"Status changed from {old_status} to {new_status}. Reason: {reason}"
        )
        db.add(audit)
        db.commit()
        db.refresh(record)

        return record
