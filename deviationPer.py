# import cv2
# import mediapipe as mp
# import numpy as np

# # Load image
# image_path = r'C:\Users\Karri\OneDrive\Desktop\Eye Yantra\JSR_Strabismus_Bluetooth_WiFi_Interface_Tests\replaced_eyes_manual.jpg'  # Change this to your actual image path
# frame = cv2.imread(image_path)
# rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# h, w, _ = frame.shape

# # Initialize MediaPipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# # Landmark indices
# LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
# LEFT_IRIS = [474, 475, 476, 477]
# RIGHT_IRIS = [469, 470, 471, 472]

# left_gaze_vector = None
# right_gaze_vector = None

# results = face_mesh.process(rgb_frame)

# if results.multi_face_landmarks:
#     for face_landmarks in results.multi_face_landmarks:
#         for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
#             points = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in eye_landmarks]
#             cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

#         for iris_indices, iris_label, eye_landmarks, color in zip(
#             [LEFT_IRIS, RIGHT_IRIS],
#             ['LEFT IRIS', 'RIGHT IRIS'],
#             [LEFT_EYE, RIGHT_EYE],
#             [(255, 0, 0), (0, 0, 255)]
#         ):
#             iris_coords = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in iris_indices]
#             for x, y in iris_coords:
#                 cv2.circle(frame, (x, y), 1, color, -1)

#             if iris_coords:
#                 center_x = int(np.mean([p[0] for p in iris_coords]))
#                 center_y = int(np.mean([p[1] for p in iris_coords]))

#                 (iris_center, radius) = cv2.minEnclosingCircle(np.array(iris_coords))
#                 iris_center = (int(iris_center[0]), int(iris_center[1]))
#                 radius = int(radius)
#                 cv2.circle(frame, iris_center, radius, color, 1)

#                 inner = np.array([int(face_landmarks.landmark[eye_landmarks[0]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[0]].y * h)])
#                 outer = np.array([int(face_landmarks.landmark[eye_landmarks[8]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[8]].y * h)])
#                 eye_mid = (inner + outer) // 2
#                 cv2.circle(frame, eye_mid, 3, (0, 255, 255), -1)

#                 gaze_vector = (eye_mid - np.array([center_x, center_y])) * -1
#                 gaze_endpoint = (int(center_x + gaze_vector[0] * 40), int(center_y + gaze_vector[1] * 40))

#                 cv2.arrowedLine(frame, (center_x, center_y), gaze_endpoint, color, 2, tipLength=0.2)
#                 cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

#                 gazevector = (center_x - gaze_endpoint[0], center_y - gaze_endpoint[1])
#                 if iris_label == 'LEFT IRIS':
#                     left_gaze_vector = gazevector
#                 elif iris_label == 'RIGHT IRIS':
#                     right_gaze_vector = gazevector

# # Analysis
# if left_gaze_vector and right_gaze_vector:
#     left_dx = left_gaze_vector[0]
#     right_dx = right_gaze_vector[0]
#     if left_dx > 0 and right_dx < 0:
#         eye_alignment = "Converging"
#     elif left_dx < 0 and right_dx > 0:
#         eye_alignment = "Diverging"
#     else:
#         eye_alignment = "Parallel/Undetermined"

#     a = np.array(left_gaze_vector, dtype=np.float32)
#     b = np.array(right_gaze_vector, dtype=np.float32)
#     norm_a = np.linalg.norm(a)
#     norm_b = np.linalg.norm(b)

#     if norm_a > 0 and norm_b > 0:
#         cos_theta = np.dot(a, b) / (norm_a * norm_b)
#         cos_theta = np.clip(cos_theta, -1.0, 1.0)
#         angle_deg = np.degrees(np.arccos(cos_theta))

#         if angle_deg < 30 or angle_deg > 150:
#             status = "Parallel"
#         else:
#             status = "Not Parallel"

#         cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
#         cv2.putText(frame, f"Eye Alignment: {eye_alignment}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
#         cv2.putText(frame, f"Status: {status}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

# # Save the output
# output_path = 'Swapoutput.jpg'
# cv2.imwrite(output_path, frame)
# print(f"Saved result to {output_path}")







# import cv2
# import mediapipe as mp
# import numpy as np

# def compute_intersection(p1, p2, q1, q2):
#     # Unpack points
#     x1, y1 = p1
#     x2, y2 = p2
#     x3, y3 = q1
#     x4, y4 = q2

#     # Compute determinants
#     denom = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 - x4)
#     if denom == 0:
#         return None  # Lines are parallel or coincident

#     # Intersection coordinates
#     px = ((x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2)*(x3*y4 - y3*x4)) / denom
#     py = ((x1*y2 - y1*x2)*(y3 - y4) - (y1 - y2)*(x3*y4 - y3*x4)) / denom

#     return int(px), int(py)

# # Load image
# image_path = r'C:\Users\Karri\Documents\A_Swap\swapped_upper.jpg' # Change to your image path
# frame = cv2.imread(image_path)
# rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# h, w, _ = frame.shape

# # Initialize MediaPipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# # Landmark indices
# LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
# LEFT_IRIS = [474, 475, 476, 477]
# RIGHT_IRIS = [469, 470, 471, 472]

# left_gaze_vector = None
# right_gaze_vector = None
# left_iris_center = None
# right_iris_center = None
# left_gaze_endpoint = None
# right_gaze_endpoint = None

# results = face_mesh.process(rgb_frame)

# def is_point_on_segment(p1, p2, pt, tolerance=30):
#     """Check if a point lies within a segment bounded by p1 and p2 (with some tolerance)."""
#     dist_total = np.linalg.norm(np.array(p2) - np.array(p1))
#     dist1 = np.linalg.norm(np.array(pt) - np.array(p1))
#     dist2 = np.linalg.norm(np.array(pt) - np.array(p2))
#     return abs((dist1 + dist2) - dist_total) <= tolerance



# if results.multi_face_landmarks:
#     for face_landmarks in results.multi_face_landmarks:
#         for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
#             points = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in eye_landmarks]
#             cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

#         for iris_indices, iris_label, eye_landmarks, color in zip(
#             [LEFT_IRIS, RIGHT_IRIS],
#             ['LEFT IRIS', 'RIGHT IRIS'],
#             [LEFT_EYE, RIGHT_EYE],
#             [(255, 0, 0), (0, 0, 255)]
#         ):
#             iris_coords = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in iris_indices]
#             for x, y in iris_coords:
#                 cv2.circle(frame, (x, y), 1, color, -1)

#             if iris_coords:
#                 center_x = int(np.mean([p[0] for p in iris_coords]))
#                 center_y = int(np.mean([p[1] for p in iris_coords]))

#                 (iris_center, radius) = cv2.minEnclosingCircle(np.array(iris_coords))
#                 iris_center = (int(iris_center[0]), int(iris_center[1]))
#                 radius = int(radius)
#                 cv2.circle(frame, iris_center, radius, color, 1)

#                 inner = np.array([int(face_landmarks.landmark[eye_landmarks[0]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[0]].y * h)])
#                 outer = np.array([int(face_landmarks.landmark[eye_landmarks[8]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[8]].y * h)])
#                 eye_mid = (inner + outer) // 2
#                 cv2.circle(frame, eye_mid, 3, (0, 255, 255), -1)

#                 gaze_vector = (eye_mid - np.array([center_x, center_y])) * -1
#                 gaze_endpoint = (int(center_x + gaze_vector[0] * 40), int(center_y + gaze_vector[1] * 40))

#                 cv2.arrowedLine(frame, (center_x, center_y), gaze_endpoint, color, 2, tipLength=0.2)
#                 cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

#                 gazevector = (center_x - gaze_endpoint[0], center_y - gaze_endpoint[1])

#                 if iris_label == 'LEFT IRIS':
#                     left_gaze_vector = gazevector
#                     left_iris_center = (center_x, center_y)
#                     left_gaze_endpoint = gaze_endpoint
#                 elif iris_label == 'RIGHT IRIS':
#                     right_gaze_vector = gazevector
#                     right_iris_center = (center_x, center_y)
#                     right_gaze_endpoint = gaze_endpoint

# # Analysis
# if left_gaze_vector and right_gaze_vector:
#     left_dx = left_gaze_vector[0]
#     right_dx = right_gaze_vector[0]
#     if left_dx > 0 and right_dx < 0:
#         eye_alignment = "Converging"
#     elif left_dx < 0 and right_dx > 0:
#         eye_alignment = "Diverging"
#     else:
#         eye_alignment = "Parallel/Undetermined"

#     a = np.array(left_gaze_vector, dtype=np.float32)
#     b = np.array(right_gaze_vector, dtype=np.float32)
#     norm_a = np.linalg.norm(a)
#     norm_b = np.linalg.norm(b)

#     if norm_a > 0 and norm_b > 0:
#         cos_theta = np.dot(a, b) / (norm_a * norm_b)
#         cos_theta = np.clip(cos_theta, -1.0, 1.0)
#         angle_deg = np.degrees(np.arccos(cos_theta))

#         if angle_deg < 30 or angle_deg > 150:
#             status = "Parallel"
#         else:
#             status = "Not Parallel"

#         cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
#         cv2.putText(frame, f"Eye Alignment: {eye_alignment}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
#         cv2.putText(frame, f"Status: {status}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

# # Gaze intersection check
# if left_iris_center and right_iris_center and left_gaze_endpoint and right_gaze_endpoint:
#     left_line = (left_iris_center, left_gaze_endpoint)
#     right_line = (right_iris_center, right_gaze_endpoint)
#     intersection = compute_intersection(*left_line, *right_line)
#     print(intersection)

#     if intersection:
#         cv2.circle(frame, intersection, 5, (0, 255, 255), -1)
#         cv2.putText(frame, "Intersect", (intersection[0] + 5, intersection[1] - 5),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
#         print(f"Gaze lines intersect at {intersection}")
#     else:
#         print("Gaze lines do not intersect (they may be parallel).")

# # Save the output
# output_path = 'Swapoutput.jpg'
# cv2.imwrite(output_path, frame)
# print(f"Saved result to {output_path}")








# #//BestCode
# import cv2
# import mediapipe as mp
# import numpy as np

# # Load image
# image_path = r'C:\Users\Karri\Documents\V_Swap\swapped_down.jpg'  # Update this path
# frame = cv2.imread(image_path)
# rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# h, w, _ = frame.shape

# # Initialize MediaPipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# # Landmark indices
# LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
# LEFT_IRIS = [474, 475, 476, 477]
# RIGHT_IRIS = [469, 470, 471, 472]

# left_gaze_vector = None
# right_gaze_vector = None
# left_iris_center = None
# right_iris_center = None

# results = face_mesh.process(rgb_frame)

# if results.multi_face_landmarks:
#     for face_landmarks in results.multi_face_landmarks:
#         # Draw eye outlines
#         for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
#             points = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in eye_landmarks]
#             cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

#         # Draw iris landmarks and process gaze
#         for iris_indices, iris_label, eye_landmarks, color in zip(
#             [LEFT_IRIS, RIGHT_IRIS],
#             ['LEFT IRIS', 'RIGHT IRIS'],
#             [LEFT_EYE, RIGHT_EYE],
#             [(255, 0, 0), (0, 0, 255)]
#         ):
#             iris_coords = [(int(face_landmarks.landmark[idx].x * w), int(face_landmarks.landmark[idx].y * h)) for idx in iris_indices]
#             for x, y in iris_coords:
#                 cv2.circle(frame, (x, y), 1, color, -1)

#             if iris_coords:
#                 center_x = int(np.mean([p[0] for p in iris_coords]))
#                 center_y = int(np.mean([p[1] for p in iris_coords]))

#                 (iris_center, radius) = cv2.minEnclosingCircle(np.array(iris_coords))
#                 iris_center = (int(iris_center[0]), int(iris_center[1]))
#                 radius = int(radius)
#                 cv2.circle(frame, iris_center, radius, color, 1)

#                 inner = np.array([int(face_landmarks.landmark[eye_landmarks[0]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[0]].y * h)])
#                 outer = np.array([int(face_landmarks.landmark[eye_landmarks[8]].x * w),
#                                   int(face_landmarks.landmark[eye_landmarks[8]].y * h)])
#                 eye_mid = (inner + outer) // 2
#                 cv2.circle(frame, eye_mid, 3, (0, 255, 255), -1)

#                 gaze_vector = (eye_mid - np.array([center_x, center_y])) * -1
#                 gaze_endpoint = (int(center_x + gaze_vector[0] * 40), int(center_y + gaze_vector[1] * 40))

#                 cv2.arrowedLine(frame, (center_x, center_y), gaze_endpoint, color, 2, tipLength=0.2)
#                 cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

#                 gazevector = (center_x - gaze_endpoint[0], center_y - gaze_endpoint[1])
#                 if iris_label == 'LEFT IRIS':
#                     left_gaze_vector = gazevector
#                     left_iris_center = iris_center
#                 elif iris_label == 'RIGHT IRIS':
#                     right_gaze_vector = gazevector
#                     right_iris_center = iris_center

# # --- Alignment Analysis ---
# if left_gaze_vector and right_gaze_vector and left_iris_center and right_iris_center:
#     left_dx = left_gaze_vector[0]
#     right_dx = right_gaze_vector[0]

#     # Method 1: Original
#     if left_dx * right_dx < 0:
#         if left_dx > 0:
#             eye_alignment = "Converging"
#         else:
#             eye_alignment = "Diverging"
#     else:
#         eye_alignment = "Parallel/Undetermined"

#     # Angle between gaze vectors
#     a = np.array(left_gaze_vector, dtype=np.float32)
#     b = np.array(right_gaze_vector, dtype=np.float32)
#     norm_a = np.linalg.norm(a)
#     norm_b = np.linalg.norm(b)

#     if norm_a > 0 and norm_b > 0:
#         cos_theta = np.dot(a, b) / (norm_a * norm_b)
#         cos_theta = np.clip(cos_theta, -1.0, 1.0)
#         angle_deg = np.degrees(np.arccos(cos_theta))

#         if angle_deg < 30 or angle_deg > 150:
#             status = "Parallel"
#         else:
#             status = "Not Parallel"

#         cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
#         cv2.putText(frame, f"Eye Alignment: {eye_alignment}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
#         cv2.putText(frame, f"Status: {status}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

#     # --- Method 2: Refined alignment using 7px gaze shift ---
#     left_unit = a / norm_a
#     right_unit = b / norm_b

#     left_gaze_point = np.array(left_iris_center, dtype=np.float32) + (-left_unit * 40)
#     right_gaze_point = np.array(right_iris_center, dtype=np.float32) + (-right_unit * 40)

#     original_iris_distance = np.linalg.norm(np.array(left_iris_center) - np.array(right_iris_center))
#     shifted_distance = np.linalg.norm(left_gaze_point - right_gaze_point)

#     diverging_Amount=0
#     converging_Amount=0
#     if shifted_distance > original_iris_distance:
#         refined_alignment = "Diverging (gaze shifted)"
#         diverging_Amount=shifted_distance - original_iris_distance
#         refined_alignment+=str(diverging_Amount)
#     elif shifted_distance < original_iris_distance:
#         refined_alignment = "Converging (gaze shifted)"
#         converging_Amount=original_iris_distance -shifted_distance
#         refined_alignment+=str(converging_Amount) 
#     else:
#         refined_alignment = "Parallel (gaze shifted)"

#     cv2.putText(frame, f"Refined: {refined_alignment}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 100), 2)

#     # Optional visualization
#     # Draw 7px gaze shifted points and connect them to iris centers (show as mini vectors)
#     cv2.arrowedLine(frame, left_iris_center,right_iris_center , (255, 100, 100), 2, tipLength=0.4)
#     cv2.arrowedLine(frame, tuple(left_gaze_point.astype(int)), tuple(right_gaze_point.astype(int)), (100, 100, 255), 2, tipLength=0.4)

#     cv2.circle(frame, tuple(left_gaze_point.astype(int)), 3, (255, 100, 100), -1)
#     cv2.circle(frame, tuple(right_gaze_point.astype(int)), 3, (100, 100, 255), -1)

#     cv2.putText(frame, "L-shift", tuple(left_gaze_point.astype(int) + np.array([5, -5])), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
#     cv2.putText(frame, "R-shift", tuple(right_gaze_point.astype(int) + np.array([5, -5])), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 255), 1)


# # Save result
# output_path = 'Swapoutput.jpg'
# cv2.imwrite(output_path, frame)
# print(f"Saved result to {output_path}")



import cv2
import numpy as np
import mediapipe as mp

# Landmark indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# MediaPipe FaceMesh (for static images)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# Eye and iris mask functions
def create_eye_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    eye_pts = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [eye_pts], 255)
    return mask

def create_iris_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    iris_pts = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_pts)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(mask, center, radius, 255, -1)
    return mask

# Load your image here (replace 'your_image.jpg' with your image file)"C:\Users\Karri\Documents\A_Swap\swapped_upper.jpg"
image_path = r'C:\Users\Karri\Documents\A_Swap\swapped_down.jpg'
frame = cv2.imread(image_path)
if frame is None:
    print(f"Error: Could not load image {image_path}")
    exit()

h, w = frame.shape[:2]
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
results = face_mesh.process(frame_rgb)

left_gaze_vector = right_gaze_vector = None
left_iris_center = right_iris_center = None

if results.multi_face_landmarks:
    for face_landmarks in results.multi_face_landmarks:
        landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

        left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
        right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
        left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
        right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

        left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
        right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)

        def process_eye(intersection, eye_landmarks, color, label):
            contours, _ = cv2.findContours(intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame, contours, -1, (0, 255, 255), 1)

            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(frame, (cx, cy), 3, color, -1)
                cv2.putText(frame, label, (cx + 5, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                inner = np.array([int(face_landmarks.landmark[eye_landmarks[0]].x * w),
                                  int(face_landmarks.landmark[eye_landmarks[0]].y * h)])
                outer = np.array([int(face_landmarks.landmark[eye_landmarks[8]].x * w),
                                  int(face_landmarks.landmark[eye_landmarks[8]].y * h)])
                eye_mid = (inner + outer) // 2
                cv2.circle(frame, tuple(eye_mid), 3, (0, 255, 255), -1)

                gaze_vector = (eye_mid - np.array([cx, cy])) * -1
                gaze_endpoint = (int(cx + gaze_vector[0] * 20), int(cy + gaze_vector[1] * 20))
                cv2.arrowedLine(frame, (cx, cy), gaze_endpoint, color, 2, tipLength=0.2)

                if label == "L-C":
                    return (gaze_vector, (cx, cy))
                else:
                    return (gaze_vector, (cx, cy))
            return None, None

        left_gaze_vector, left_iris_center = process_eye(left_intersection, LEFT_EYE, (0, 0, 255), "L-C")
        right_gaze_vector, right_iris_center = process_eye(right_intersection, RIGHT_EYE, (255, 0, 0), "R-C")

        left_area = cv2.countNonZero(left_intersection)
        right_area = cv2.countNonZero(right_intersection)
        cv2.putText(frame, f"L:{left_area} R:{right_area}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

# Gaze vector comparison and display
if left_gaze_vector is not None and right_gaze_vector is not None:
    left_dx = left_gaze_vector[0]
    right_dx = right_gaze_vector[0]

    if left_dx * right_dx < 0:
        eye_alignment = "Converging" if left_dx > 0 else "Diverging"
    else:
        eye_alignment = "Parallel/Undetermined"

    a = np.array(left_gaze_vector, dtype=np.float32)
    b = np.array(right_gaze_vector, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a > 0 and norm_b > 0:   
        cos_theta = np.dot(a, b) / (norm_a * norm_b)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        angle_deg = np.degrees(np.arccos(cos_theta))

        if angle_deg < 30 or angle_deg > 150:
            status = "Parallel"
        else:
            status = "Not Parallel"

        cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Eye Alignment: {eye_alignment}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
        cv2.putText(frame, f"Status: {status}", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

        # Refined shift-based divergence check
        left_unit = a / norm_a
        right_unit = b / norm_b
        left_gaze_point = np.array(left_iris_center, dtype=np.float32) + (left_unit * 40)
        right_gaze_point = np.array(right_iris_center, dtype=np.float32) + (right_unit * 40)
        cv2.arrowedLine(frame, left_iris_center,right_iris_center , (255, 100, 100), 2, tipLength=0.4)
        cv2.arrowedLine(frame, tuple(left_gaze_point.astype(int)), tuple(right_gaze_point.astype(int)), (100, 100, 255), 2, tipLength=0.4)

        original_dist = np.linalg.norm(np.array(left_iris_center) - np.array(right_iris_center))
        print(original_dist)
        shifted_dist = np.linalg.norm(left_gaze_point - right_gaze_point)

        if shifted_dist > original_dist:
            refined_alignment = f"Diverging ({shifted_dist - original_dist:.2f}px)"
        elif shifted_dist < original_dist:
            refined_alignment = f"Converging ({original_dist - shifted_dist:.2f}px)"
        else:
            refined_alignment = "Parallel"

        cv2.putText(frame, f"Refined: {refined_alignment}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2)

# Show result image
cv2.imshow("Gaze Vector from Iris-Eye Intersection", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
