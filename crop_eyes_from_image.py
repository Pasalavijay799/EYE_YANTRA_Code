import cv2
import mediapipe as mp
import numpy as np
import os

# Initialize Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
)

# Left and right eye landmarks (dense region)
LEFT_EYE = [33, 133, 159, 145, 153, 154, 155, 246]
RIGHT_EYE = [362, 263, 386, 374, 380, 381, 382, 398]

def crop_eyes_from_image(image_path, padding=40):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or unreadable.")

    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_height, img_width = image.shape[:2]
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        raise ValueError("No face detected in the image.")

    for face_landmarks in results.multi_face_landmarks:
        # Get coordinates of both eyes
        eye_indices = LEFT_EYE + RIGHT_EYE
        eye_coords = [
            (
                int(face_landmarks.landmark[idx].x * img_width),
                int(face_landmarks.landmark[idx].y * img_height)
            )
            for idx in eye_indices
            if idx < len(face_landmarks.landmark)
        ]

        eye_coords = np.array(eye_coords)

        # Bounding box for both eyes
        x, y, w, h = cv2.boundingRect(eye_coords)

        # Add padding
        x1 = max(x - padding, 0)
        y1 = max(y - padding, 0)
        x2 = min(x + w + padding, img_width)
        y2 = min(y + h + padding, img_height)

        # Match original aspect ratio
        original_ratio = img_width / img_height
        crop_w = x2 - x1
        crop_h = y2 - y1
        current_ratio = crop_w / crop_h

        if current_ratio > original_ratio:
            # Too wide, increase height
            new_h = crop_w / original_ratio
            center_y = (y1 + y2) // 2
            y1 = int(center_y - new_h / 2)
            y2 = int(center_y + new_h / 2)
        else:
            # Too tall, increase width
            new_w = crop_h * original_ratio
            center_x = (x1 + x2) // 2
            x1 = int(center_x - new_w / 2)
            x2 = int(center_x + new_w / 2)

        # Clamp to bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img_width, x2), min(img_height, y2)

        # Crop and overwrite the original image
        cropped = image[y1:y2, x1:x2]
        cv2.imwrite(image_path, cropped)
        return True

    raise RuntimeError("Unexpected error: no face landmarks processed.")
