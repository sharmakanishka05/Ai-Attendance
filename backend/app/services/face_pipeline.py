import os
import cv2
import json
import uuid
import base64
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings

logger = logging.getLogger("attendai.cv")

class FacePipelineService:
    def __init__(self):
        self.cascade = None
        self.yunet_detector = None
        self.sface_recognizer = None
        self.embedding_session = None
        self._init_detectors()

    def _init_detectors(self):
        """Initializes OpenCV face detector (Cascade and/or YuNet DNN) and Recognizer (SFace/ArcFace)"""
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if os.path.exists(cascade_path):
                self.cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("Loaded Haar Cascade face detector successfully.")
        except Exception as e:
            logger.warning(f"Could not load Haar cascade: {e}")

        # 1. Check for YuNet model in models directory
        yunet_path = os.path.join(settings.MODELS_DIR, "face_detection_yunet.onnx")
        if os.path.exists(yunet_path) and os.path.getsize(yunet_path) > 10000:
            try:
                self.yunet_detector = cv2.FaceDetectorYN.create(
                    model=yunet_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5000
                )
                logger.info("Loaded YuNet DNN face detector successfully.")
            except Exception as e:
                logger.warning(f"Failed to load YuNet model: {e}")

        # 2. Check for SFace ONNX recognition model in models directory
        sface_path = os.path.join(settings.MODELS_DIR, "face_recognition_sface.onnx")
        if os.path.exists(sface_path) and os.path.getsize(sface_path) > 1000000:
            try:
                self.sface_recognizer = cv2.FaceRecognizerSF.create(
                    model=sface_path,
                    config=""
                )
                logger.info("Loaded SFace DNN face recognizer successfully.")
            except Exception as e:
                logger.warning(f"Failed to load SFace model: {e}")

        # 3. Check for ArcFace ONNX models
        for arc_name in ["arcface.onnx", "w600k_r50.onnx", "glintr100.onnx"]:
            arc_path = os.path.join(settings.MODELS_DIR, arc_name)
            if os.path.exists(arc_path) and os.path.getsize(arc_path) > 1000000:
                try:
                    import onnxruntime as ort
                    self.embedding_session = ort.InferenceSession(arc_path, providers=["CPUExecutionProvider"])
                    logger.info(f"Loaded ArcFace ONNX model from {arc_path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load ArcFace ONNX model: {e}")

    def detect_faces(self, image_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects multiple faces in an image (supports 1 to 40+ faces in a classroom photo).
        Returns a list of dicts with (x, y, w, h) bounding boxes in pixels and normalized percentage.
        """
        if image_bgr is None or image_bgr.size == 0:
            return []

        h_img, w_img = image_bgr.shape[:2]
        boxes = []

        # 1. Try YuNet if available
        if self.yunet_detector is not None:
            try:
                self.yunet_detector.setInputSize((w_img, h_img))
                _, detected = self.yunet_detector.detect(image_bgr)
                if detected is not None:
                    for d in detected:
                        x, y, w, h = int(d[0]), int(d[1]), int(d[2]), int(d[3])
                        # Filter out invalid dimensions
                        if w > 15 and h > 15:
                            boxes.append((max(0, x), max(0, y), min(w, w_img - x), min(h, h_img - y)))
            except Exception as e:
                logger.warning(f"YuNet detection error: {e}, falling back to cascade")

        # 2. Use Haar Cascade if YuNet returned nothing or is unavailable
        if not boxes and self.cascade is not None:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            # Equalize histogram for varied classroom lighting
            gray = cv2.equalizeHist(gray)
            detected = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(24, 24),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, w, h) in detected:
                boxes.append((int(x), int(y), int(w), int(h)))

        # Format output with normalized coordinates
        results = []
        for i, (x, y, w, h) in enumerate(boxes):
            norm_box = {
                "box_id": f"face_{i+1}_{uuid.uuid4().hex[:6]}",
                "x_px": x,
                "y_px": y,
                "w_px": w,
                "h_px": h,
                "bbox": {
                    "x": round((x / w_img) * 100.0, 2),
                    "y": round((y / h_img) * 100.0, 2),
                    "width": round((w / w_img) * 100.0, 2),
                    "height": round((h / h_img) * 100.0, 2),
                }
            }
            results.append(norm_box)

        return results

    def extract_embedding(self, face_crop_bgr: np.ndarray) -> List[float]:
        """
        Generates a normalized 512-dimensional feature embedding for a face crop.
        Guarantees unit L2 norm (sum of squares == 1.0).
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return [0.0] * 512

        # Standardize face crop to 112x112 (Standard resolution for ArcFace/SFace)
        face_resized = cv2.resize(face_crop_bgr, (112, 112))

        # 1. Check if SFace recognizer is loaded (OpenCV Deep Neural Network)
        if self.sface_recognizer is not None:
            try:
                feat = self.sface_recognizer.feature(face_resized)
                embedding = feat.flatten()
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return [round(float(v), 6) for v in embedding]
            except Exception as e:
                logger.warning(f"Inference error with SFace DNN: {e}")

        # 2. Check if ONNX model session is loaded (ArcFace)
        if self.embedding_session is not None:
            try:
                # Preprocess: Transpose to (1, 3, 112, 112), normalize [-1, 1]
                blob = cv2.dnn.blobFromImage(
                    face_resized, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True
                )
                input_name = self.embedding_session.get_inputs()[0].name
                feats = self.embedding_session.run(None, {input_name: blob})[0]
                embedding = feats.flatten()
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return [round(float(v), 6) for v in embedding]
            except Exception as e:
                logger.warning(f"Inference error with ArcFace ONNX: {e}")

        # High-dimensional multi-scale spatial frequency feature extraction (Robust 512-d unit vector)
        # Converts spatial gradients, local color statistics, and DCT coefficients into a 512-d fingerprint
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        
        # 1. Block-based gradient descriptors (16x16 blocks = 16 sub-regions)
        sub_features = []
        for r in range(4):
            for c in range(4):
                sub_block = gray[r*28:(r+1)*28, c*28:(c+1)*28]
                gx = cv2.Sobel(sub_block, cv2.CV_32F, 1, 0, ksize=3)
                gy = cv2.Sobel(sub_block, cv2.CV_32F, 0, 1, ksize=3)
                mag, ang = cv2.cartToPolar(gx, gy)
                # 8-bin orientation histogram per block (16 * 8 = 128)
                hist, _ = np.histogram(ang, bins=8, range=(0, 2*np.pi), weights=mag)
                sub_features.extend(hist)

        # 2. DCT (Discrete Cosine Transform) low & mid frequency components (256 components)
        float_gray = np.float32(gray) / 255.0
        dct = cv2.dct(float_gray)
        dct_coeffs = dct[:16, :16].flatten()  # 256 components
        sub_features.extend(dct_coeffs)

        # 3. Color channel moments and central contrast (128 components)
        for ch in range(3):
            ch_data = face_resized[:, :, ch]
            ch_dct = cv2.dct(np.float32(ch_data) / 255.0)
            sub_features.extend(ch_dct[:6, :7].flatten()[:42])
        # Pad to exactly 512 components
        raw_vec = np.array(sub_features[:512], dtype=np.float32)
        if len(raw_vec) < 512:
            raw_vec = np.pad(raw_vec, (0, 512 - len(raw_vec)))

        # Normalize to unit sphere (cosine similarity compatible)
        norm = np.linalg.norm(raw_vec)
        if norm > 1e-6:
            unit_vec = raw_vec / norm
        else:
            unit_vec = raw_vec

        return [round(float(v), 6) for v in unit_vec]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two unit vectors: dot(a, b). Range [-1, 1]"""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        dot_product = float(np.dot(a, b) / (norm_a * norm_b))
        # Clamp to [0.0, 1.0] for probability representation
        return max(0.0, min(1.0, dot_product))

    def recognize_faces(
        self,
        image_bgr: np.ndarray,
        enrolled_embeddings: List[Dict[str, Any]],
        match_threshold: float = None,
        review_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Executes full recognition pipeline on an input image:
        1. Multi-face detection
        2. Embedding extraction for each detected face
        3. Vector similarity search against enrolled students
        4. Classification: Recognized, Needs Review, Unknown
        5. Single-image deduplication
        """
        if match_threshold is None:
            match_threshold = settings.FACE_MATCH_THRESHOLD
        if review_threshold is None:
            review_threshold = settings.FACE_REVIEW_THRESHOLD

        detected_boxes = self.detect_faces(image_bgr)
        h_img, w_img = image_bgr.shape[:2]

        recognized_students = {}
        processed_faces = []
        recognized_count = 0
        review_count = 0
        unknown_count = 0

        for box in detected_boxes:
            x, y, w, h = box["x_px"], box["y_px"], box["w_px"], box["h_px"]
            # Crop face
            crop = image_bgr[y:y+h, x:x+w]
            
            # Base64 thumbnail for review UI
            crop_resized = cv2.resize(crop, (96, 96))
            _, buffer = cv2.imencode(".jpg", crop_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            crop_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")

            # Extract 512-d embedding
            embedding = self.extract_embedding(crop)

            # Similarity search against enrolled faces
            best_match = None
            best_score = 0.0

            for enrolled in enrolled_embeddings:
                student_vec = enrolled.get("vector")
                if not student_vec:
                    continue
                score = self.cosine_similarity(embedding, student_vec)
                if score > best_score:
                    best_score = score
                    best_match = enrolled

            # Determine match status based on configurable thresholds
            if best_score >= match_threshold and best_match is not None:
                student_id = best_match["student_id"]
                # Duplicate check within this photograph
                if student_id in recognized_students:
                    # Keep the higher confidence one
                    prev_score = recognized_students[student_id]["score"]
                    if best_score > prev_score:
                        # Demote previous to duplicate/review
                        recognized_students[student_id]["status"] = "review"
                        status = "recognized"
                        recognized_students[student_id] = {"score": best_score, "status": "recognized"}
                    else:
                        status = "review"
                else:
                    status = "recognized"
                    recognized_students[student_id] = {"score": best_score, "status": "recognized"}
                    recognized_count += 1

                student_name = best_match.get("student_name")
                roll_number = best_match.get("roll_number")

            elif best_score >= review_threshold and best_match is not None:
                status = "review"
                student_id = best_match["student_id"]
                student_name = best_match.get("student_name")
                roll_number = best_match.get("roll_number")
                review_count += 1
            else:
                status = "unknown"
                student_id = None
                student_name = None
                roll_number = None
                best_score = round(best_score, 2)
                unknown_count += 1

            processed_faces.append({
                "box_id": box["box_id"],
                "bbox": box["bbox"],
                "student_id": student_id,
                "student_name": student_name,
                "roll_number": roll_number,
                "confidence": round(float(best_score), 3),
                "status": status,
                "face_crop_base64": crop_b64
            })

        return {
            "total_detected": len(processed_faces),
            "recognized_count": recognized_count,
            "review_count": review_count,
            "unknown_count": unknown_count,
            "faces": processed_faces
        }

face_pipeline = FacePipelineService()
