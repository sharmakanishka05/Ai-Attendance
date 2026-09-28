import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models import (
    User, ClassModel, Student, FaceEmbedding, SystemSetting
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

REAL_MCA_STUDENTS = [
    {
        "id": "MCA001",
        "name": "Kanishka Sharma",
        "roll_number": "MCA001",
        "email": "kanishka.mca001@kit.ac.in",
        "course": "MCA",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year"
    },
    {
        "id": "MCA002",
        "name": "Namita Jain",
        "roll_number": "MCA002",
        "email": "namita.mca002@kit.ac.in",
        "course": "MCA",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year"
    },
    {
        "id": "MCA003",
        "name": "Akanksha Mishra",
        "roll_number": "MCA003",
        "email": "akanksha.mca003@kit.ac.in",
        "course": "MCA",
        "class_name": "MCA Final Year",
        "section": "MCA Final Year"
    }
]

def seed_database(db: Session):
    # 1. Purge legacy placeholder accounts completely
    db.query(User).filter(User.email.in_(["alex.roberts@attendai.edu", "sarah.chen@attendai.edu"])).delete(synchronize_session=False)
    db.commit()

    # 2. Ensure single administrator account: Ajeet Singh
    admin = db.query(User).filter(User.email == "ajeet.singh@kit.ac.in").first()
    if not admin:
        print("[KIT Kanpur] Seeding database with official MCA Final Year roster and instructor Ajeet Singh...")
        admin = User(
            email="ajeet.singh@kit.ac.in",
            hashed_password=pwd_context.hash("password123"),
            full_name="Ajeet Singh",
            role="admin"
        )
        db.add(admin)
        db.commit()
    else:
        admin.full_name = "Ajeet Singh"
        admin.role = "admin"
        admin.hashed_password = pwd_context.hash("password123")
        db.commit()

    # 3. Single Class: MCA Final Year
    c_mca = db.query(ClassModel).filter(ClassModel.id == "class_mca_final").first()
    if not c_mca:
        c_mca = ClassModel(
            id="class_mca_final",
            name="MCA",
            course="MCA",
            section="MCA Final Year",
            teacher_id=admin.id,
            teacher_name="Ajeet Singh",
            schedule="Mon-Fri 09:30 AM"
        )
        db.add(c_mca)
        db.commit()
    else:
        c_mca.name = "MCA"
        c_mca.course = "MCA"
        c_mca.section = "MCA Final Year"
        c_mca.teacher_id = admin.id
        c_mca.teacher_name = "Ajeet Singh"
        db.commit()

    # 4. Exact 3 Students
    students = []
    for s_info in REAL_MCA_STUDENTS:
        sid = s_info["id"]
        st = db.query(Student).filter((Student.id == sid) | (Student.roll_number == s_info["roll_number"])).first()
        if not st:
            st = Student(
                id=sid,
                name=s_info["name"],
                roll_number=s_info["roll_number"],
                email=s_info["email"],
                course=s_info["course"],
                class_name=s_info["class_name"],
                section=s_info["section"],
                status="active"
            )
            st.classes.append(c_mca)
            db.add(st)
            db.flush()
        else:
            st.name = s_info["name"]
            st.roll_number = s_info["roll_number"]
            st.email = s_info["email"]
            st.course = s_info["course"]
            st.class_name = s_info["class_name"]
            st.section = s_info["section"]
            st.status = "active"
            if c_mca not in st.classes:
                st.classes.append(c_mca)
        students.append(st)

    db.commit()

    # 4b. Seed Face Embeddings for 3 MCA students
    try:
        from app.seed_embeddings_data import SEED_EMBEDDINGS
        for emb_data in SEED_EMBEDDINGS:
            existing_emb = db.query(FaceEmbedding).filter(FaceEmbedding.id == emb_data["id"]).first()
            if not existing_emb:
                new_emb = FaceEmbedding(
                    id=emb_data["id"],
                    student_id=emb_data["student_id"],
                    embedding_json=emb_data["embedding_json"],
                    photo_path=emb_data.get("photo_path"),
                    quality_score=emb_data.get("quality_score", 1.0),
                    is_primary=emb_data.get("is_primary", True),
                    image_type=emb_data.get("image_type", "face_crop"),
                    dataset_type=emb_data.get("dataset_type", "PRODUCTION"),
                    model_name=emb_data.get("model_name", "SFace ONNX"),
                    model_version=emb_data.get("model_version", "1.0"),
                )
                db.add(new_emb)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[KIT Kanpur] Notice: could not seed face embeddings: {e}")

    # 5. Persistent System Settings (idempotent check)
    s1 = db.query(SystemSetting).filter(SystemSetting.key == "FACE_MATCH_THRESHOLD").first()
    if not s1:
        setting1 = SystemSetting(
            key="FACE_MATCH_THRESHOLD",
            value="0.70",
            description="Minimum cosine similarity for high-confidence match",
            updated_by_id=admin.id
        )
        db.add(setting1)
    
    s2 = db.query(SystemSetting).filter(SystemSetting.key == "FACE_REVIEW_THRESHOLD").first()
    if not s2:
        setting2 = SystemSetting(
            key="FACE_REVIEW_THRESHOLD",
            value="0.52",
            description="Threshold below which face is classified as unknown",
            updated_by_id=admin.id
        )
        db.add(setting2)
    
    db.commit()
    print("[KIT Kanpur] Database seeded successfully with Ajeet Singh admin, MCA Final Year class, 3 students, their face embeddings, and system settings!")
