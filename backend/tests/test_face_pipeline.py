import numpy as np
from app.services.face_pipeline import face_pipeline
from app.services.quality_check import ImageQualityChecker

def test_face_pipeline_zero_faces():
    # Plain black image has 0 faces
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    detected = face_pipeline.detect_faces(blank_img)
    assert len(detected) == 0

def test_quality_checker():
    # 1. Dark image check
    dark_img = np.ones((100, 100, 3), dtype=np.uint8) * 10
    dark_res = ImageQualityChecker.evaluate_face_image(dark_img)
    assert dark_res["checks"]["good_lighting"] is False

    # 2. Normal contrast synthetic image
    normal_img = np.random.randint(80, 180, (100, 100, 3), dtype=np.uint8)
    normal_res = ImageQualityChecker.evaluate_face_image(normal_img)
    assert normal_res["checks"]["good_lighting"] is True

def test_cosine_similarity_identity_and_orthogonality():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]

    # Identical vectors should yield similarity 1.0
    sim_identical = face_pipeline.cosine_similarity(vec_a, vec_b)
    assert round(sim_identical, 2) == 1.0

    # Orthogonal vectors should yield similarity 0.0
    sim_orthogonal = face_pipeline.cosine_similarity(vec_a, vec_c)
    assert round(sim_orthogonal, 2) == 0.0

def test_face_recognition_threshold_classification():
    # Dummy embedding representation
    synthetic_student_vec = [1.0] + [0.0] * 511
    enrolled = [{
        "student_id": "test_s1",
        "student_name": "Test Student",
        "roll_number": "CS-999",
        "vector": synthetic_student_vec
    }]

    # High match >= 0.70
    score_high = face_pipeline.cosine_similarity(synthetic_student_vec, synthetic_student_vec)
    assert score_high >= 0.70

    # Low match < 0.52
    unrelated_vec = [0.0] * 511 + [1.0]
    score_low = face_pipeline.cosine_similarity(synthetic_student_vec, unrelated_vec)
    assert score_low < 0.52
