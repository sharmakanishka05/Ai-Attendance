import cv2
import numpy as np
from typing import Dict, Any, Tuple

class ImageQualityChecker:
    @staticmethod
    def evaluate_face_image(image_bgr: np.ndarray, bbox: Tuple[int, int, int, int] = None) -> Dict[str, Any]:
        """
        Evaluates face quality: lighting, sharpness, face size/resolution, and centering.
        bbox is optional (x, y, w, h). If not provided, evaluates the entire cropped face image.
        """
        if image_bgr is None or image_bgr.size == 0:
            return {
                "overall_pass": False,
                "score": 0.0,
                "feedback": ["Invalid or empty image data."],
                "checks": {
                    "good_lighting": False,
                    "clearly_visible": False,
                    "face_centered": False,
                    "sharpness": False
                }
            }

        h_img, w_img = image_bgr.shape[:2]

        if bbox is not None:
            x, y, w, h = bbox
            # Clip bounds
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)
            if w <= 0 or h <= 0:
                face_crop = image_bgr
            else:
                face_crop = image_bgr[y:y+h, x:x+w]
        else:
            face_crop = image_bgr
            x, y, w, h = 0, 0, w_img, h_img

        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

        # 1. Lighting Check (Mean Luminance)
        mean_brightness = float(np.mean(gray))
        lighting_pass = 50.0 <= mean_brightness <= 215.0
        if mean_brightness < 50.0:
            lighting_msg = "Lighting is too dark. Increase ambient light."
        elif mean_brightness > 215.0:
            lighting_msg = "Lighting is too bright or overexposed."
        else:
            lighting_msg = "Good lighting ✓"

        # 2. Sharpness / Blur Check (Laplacian Variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sharpness_pass = laplacian_var >= 45.0
        if not sharpness_pass:
            sharpness_msg = "Face is blurry or out of focus. Hold still."
        else:
            sharpness_msg = "Face clearly visible ✓"

        # 3. Size / Resolution Check
        min_dim = min(w, h)
        size_pass = min_dim >= 40
        if not size_pass:
            size_msg = "Face is too small. Move closer to the camera."
        else:
            size_msg = "Resolution adequate ✓"

        # 4. Centering Check (relative to full image)
        if bbox is not None and w_img > 0 and h_img > 0:
            face_center_x = x + w / 2.0
            face_center_y = y + h / 2.0
            x_offset = abs(face_center_x - (w_img / 2.0)) / (w_img / 2.0)
            y_offset = abs(face_center_y - (h_img / 2.0)) / (h_img / 2.0)
            centered_pass = x_offset < 0.65 and y_offset < 0.65
            if not centered_pass:
                centered_msg = "Face is not centered. Center face in frame."
            else:
                centered_msg = "Face centered ✓"
        else:
            centered_pass = True
            centered_msg = "Face centered ✓"

        checks = {
            "good_lighting": lighting_pass,
            "clearly_visible": sharpness_pass and size_pass,
            "face_centered": centered_pass,
            "sharpness": sharpness_pass
        }

        # Calculate score (0.0 to 1.0)
        score_components = [
            1.0 if lighting_pass else 0.4,
            min(1.0, laplacian_var / 150.0),
            1.0 if size_pass else 0.5,
            1.0 if centered_pass else 0.6
        ]
        score = round(float(np.mean(score_components)), 2)

        feedback = []
        if lighting_pass:
            feedback.append(lighting_msg)
        else:
            feedback.append(lighting_msg)

        if sharpness_pass:
            feedback.append(sharpness_msg)
        else:
            feedback.append(sharpness_msg)

        if centered_pass:
            feedback.append(centered_msg)
        else:
            feedback.append(centered_msg)

        overall_pass = lighting_pass and sharpness_pass and size_pass

        return {
            "overall_pass": overall_pass,
            "score": score,
            "feedback": feedback,
            "checks": checks,
            "metrics": {
                "brightness": round(mean_brightness, 1),
                "sharpness": round(laplacian_var, 1),
                "width": int(w),
                "height": int(h)
            }
        }
