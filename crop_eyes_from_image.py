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
        print(f"⚠️ Image not found or unreadable: {image_path}")
        return False

    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_height, img_width = image.shape[:2]
    results = face_mesh.process(img_rgb)

    landmarks = None
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
    else:
        # Fallback 1: Search for the clean unannotated original image in input folders
        filename = os.path.basename(image_path)
        
        # Strip prefixes
        clean_filename = filename
        if filename.startswith("processed_hirschberg_"):
            clean_filename = filename.replace("processed_hirschberg_", "")
        elif filename.startswith("processed_"):
            clean_filename = filename.replace("processed_", "")
        elif filename.startswith("hirschberg_"):
            clean_filename = filename.replace("hirschberg_", "")
            
        possible_paths = [
            os.path.join("Preliminary", clean_filename),
            os.path.join("Hirschberg", clean_filename),
            os.path.join("Preliminary_Results", clean_filename),
            os.path.join("Hirschberg_Results", clean_filename),
            os.path.abspath(os.path.join("Preliminary", clean_filename)),
            os.path.abspath(os.path.join("Hirschberg", clean_filename)),
        ]
        
        for clean_path in possible_paths:
            if os.path.exists(clean_path):
                clean_img = cv2.imread(clean_path)
                if clean_img is not None:
                    clean_rgb = cv2.cvtColor(clean_img, cv2.COLOR_BGR2RGB)
                    clean_results = face_mesh.process(clean_rgb)
                    if clean_results.multi_face_landmarks:
                        landmarks = clean_results.multi_face_landmarks[0]
                        img_height, img_width = clean_img.shape[:2]
                        print(f"✅ Found face landmarks in clean source image: {clean_path}")
                        break
        
    if landmarks is None:
        # Fallback 2: Center horizontal crop if no landmarks can be detected
        print(f"⚠️ No face landmarks detected for {image_path}, falling back to center-strip crop.")
        y1 = int(img_height * 0.35)
        y2 = int(img_height * 0.65)
        x1 = int(img_width * 0.1)
        x2 = int(img_width * 0.9)
        cropped = image[y1:y2, x1:x2]
        cv2.imwrite(image_path, cropped)
        return True

    # Get coordinates of both eyes
    eye_indices = LEFT_EYE + RIGHT_EYE
    eye_coords = [
        (
            int(landmarks.landmark[idx].x * img_width),
            int(landmarks.landmark[idx].y * img_height)
        )
        for idx in eye_indices
        if idx < len(landmarks.landmark)
    ]

    eye_coords = np.array(eye_coords)
    x, y, w, h = cv2.boundingRect(eye_coords)

    # Add padding to cover brow and outer cheek areas
    x_pad = int(w * 0.2) + padding
    y_pad = int(h * 0.4) + padding

    x1 = max(x - x_pad, 0)
    y1 = max(y - y_pad, 0)
    x2 = min(x + w + x_pad, img_width)
    y2 = min(y + h + y_pad, img_height)

    # Crop and overwrite the original image
    cropped = image[y1:y2, x1:x2]
    cv2.imwrite(image_path, cropped)
    return True
