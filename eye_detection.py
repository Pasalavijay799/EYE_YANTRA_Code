# import cv2
# import mediapipe as mp
# import numpy as np
# import math
# import os

# # Initialize Mediapipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=True,  # Change to True for single image processing
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
# )

# # Eye Landmarks
# LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

# # Function to calculate Eye Aspect Ratio (EAR)
# def eye_aspect_ratio(landmarks, img_width, img_height):
#     def to_pixel_coords(landmark):
#         return int(landmark.x * img_width), int(landmark.y * img_height)

#     # Right Eye
#     rh_right = to_pixel_coords(landmarks[33])
#     rh_left = to_pixel_coords(landmarks[133])
#     rv_top = to_pixel_coords(landmarks[159])
#     rv_bottom = to_pixel_coords(landmarks[145])

#     # Left Eye
#     lh_right = to_pixel_coords(landmarks[362])
#     lh_left = to_pixel_coords(landmarks[263])
#     lv_top = to_pixel_coords(landmarks[386])
#     lv_bottom = to_pixel_coords(landmarks[374])

#     # Calculate distances
#     def euclidean_distance(point1, point2):
#         return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

#     rh_distance = euclidean_distance(rh_right, rh_left)
#     rv_distance = euclidean_distance(rv_top, rv_bottom)
#     lh_distance = euclidean_distance(lh_right, lh_left)
#     lv_distance = euclidean_distance(lv_top, lv_bottom)

#     # EAR Calculation
#     if rv_distance == 0 or lv_distance == 0:
#         return None, None  # Prevent division by zero

#     right_ear = rh_distance / rv_distance
#     left_ear = lh_distance / lv_distance

#     return right_ear, left_ear

# # Function to check if eyes are open or closed
# def check_eye_status(image_path):
#     image = cv2.imread(image_path)
#     if image is None:
#         return "❌ Image not found"

#     img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     img_height, img_width = image.shape[:2]

#     results = face_mesh.process(img_rgb)

#     if results.multi_face_landmarks:
#         for face_landmarks in results.multi_face_landmarks:
#             re_ratio, le_ratio = eye_aspect_ratio(face_landmarks.landmark, img_width, img_height)

#             if re_ratio is None or le_ratio is None:
#                 return "❌ Could not detect eyes"

#             closed_threshold = 6  # Adjust threshold if needed

#             if re_ratio >= closed_threshold and le_ratio >= closed_threshold:
#                 return "⚠️ Both eyes closed. Please take another capture."
#             elif re_ratio >= closed_threshold:
#                 return "⚠️ Right eye closed. Please take another capture."
#             elif le_ratio >= closed_threshold:
#                 return "⚠️ Left eye closed. Please take another capture."

#             return "✅ Eyes are open"

#     return "❌⚠️ No face detected"




import cv2
import mediapipe as mp
import numpy as np
import math

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
)

# Eye landmark groups based on Mediapipe's 468 landmarks
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]  # [p1, p2, p3, p4, p5, p6]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]  # [p1, p2, p3, p4, p5, p6]

def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_ear(eye_landmarks):
    # EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    vertical1 = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    vertical2 = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    horizontal = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear

def get_eye_landmarks(landmarks, indices, img_width, img_height):
    return [(int(landmarks[idx].x * img_width), int(landmarks[idx].y * img_height)) for idx in indices]

def check_eye_status(image_path, threshold=0.25):
    image = cv2.imread(image_path)
    if image is None:
        return "❌ Image not found or unreadable.error"

    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_height, img_width = image.shape[:2]
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        return "❌⚠️ No face detected.error"

    for face_landmarks in results.multi_face_landmarks:
        left_eye = get_eye_landmarks(face_landmarks.landmark, LEFT_EYE_INDICES, img_width, img_height)
        right_eye = get_eye_landmarks(face_landmarks.landmark, RIGHT_EYE_INDICES, img_width, img_height)

        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)

        # Evaluate based on EAR threshold
        left_closed = left_ear < threshold
        right_closed = right_ear < threshold

        if left_closed and right_closed:
            return "⚠️ Both eyes closed error. Please take another capture."
        elif left_closed:
            return "⚠️ Left eye closed error. Please take another capture."
        elif right_closed:
            return "⚠️ Right eye closed error. Please take another capture."
        else:
            return "✅ Eyes are open."

    return "❌ Unexpected error."
