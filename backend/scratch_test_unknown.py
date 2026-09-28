import os
import shutil
import cv2
import numpy as np
import sys
sys.path.insert(0, ".")
from app.services.face_pipeline import face_pipeline

gen_img_path = r"C:\Users\Ayush Dwivedi\.gemini\antigravity-ide\brain\c8d5fe72-6349-4f07-8c93-55fc261123ba\unknown_student_face_1790498138029.jpg"
backend_dest = r"data\test_data\images\unknown_person.jpg"
frontend_dest = r"..\frontend\public\test_data\unknown_person.jpg"
os.makedirs(os.path.dirname(frontend_dest), exist_ok=True)
os.makedirs(os.path.dirname(backend_dest), exist_ok=True)
shutil.copy2(gen_img_path, backend_dest)
shutil.copy2(gen_img_path, frontend_dest)

img = cv2.imread(backend_dest)
detected = face_pipeline.detect_faces(img)
print("Detected faces in unknown_person:", len(detected))

crop = img[detected[0]["y_px"]:detected[0]["y_px"]+detected[0]["h_px"], detected[0]["x_px"]:detected[0]["x_px"]+detected[0]["w_px"]]
unk_emb = face_pipeline.extract_embedding(crop)

# Compare with test images
media_dir = r"data\test_data\images"
for sid, fname in [("MCA001", "MCA001_Kanishka_Sharma.jpg"), ("MCA002", "MCA002_Namita_Jain.jpg"), ("MCA003", "MCA003_Akanksha_Mishra.jpg")]:
    m_img = cv2.imread(os.path.join(media_dir, fname))
    d = face_pipeline.detect_faces(m_img)
    m_crop = m_img[d[0]["y_px"]:d[0]["y_px"]+d[0]["h_px"], d[0]["x_px"]:d[0]["x_px"]+d[0]["w_px"]]
    m_emb = face_pipeline.extract_embedding(m_crop)
    sim = face_pipeline.cosine_similarity(unk_emb, m_emb)
    print(f"Similarity with {sid}: {sim:.4f}")
