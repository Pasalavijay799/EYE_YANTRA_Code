# import cv2
# import numpy as np
# import mediapipe as mp

# # Eye and Iris Landmark Indices
# LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
# RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
# LEFT_IRIS = [474, 475, 476, 477]
# RIGHT_IRIS = [469, 470, 471, 472]

# # Initialize MediaPipe FaceMesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

# # Create mask for eye
# def create_eye_mask(image_shape, landmarks, points):
#     mask = np.zeros(image_shape[:2], dtype=np.uint8)
#     eye_pts = np.array([landmarks[p] for p in points], dtype=np.int32)
#     cv2.fillPoly(mask, [eye_pts], 255)
#     return mask

# # Create mask for iris
# def create_iris_mask(image_shape, landmarks, points):
#     mask = np.zeros(image_shape[:2], dtype=np.uint8)
#     iris_pts = np.array([landmarks[p] for p in points], dtype=np.float32)
#     (x, y), radius = cv2.minEnclosingCircle(iris_pts)
#     center, radius = (int(x), int(y)), int(radius)
#     cv2.circle(mask, center, radius, 255, -1)
#     return mask

# # Start Webcam
# cap = cv2.VideoCapture(0)

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     img_height, img_width = frame.shape[:2]
#     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results = face_mesh.process(frame_rgb)

#     if results.multi_face_landmarks:
#         for face_landmarks in results.multi_face_landmarks:
#             # Convert landmarks to pixel coordinates
#             landmarks = [(int(lm.x * img_width), int(lm.y * img_height)) for lm in face_landmarks.landmark]

#             # Create masks
#             left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
#             right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
#             left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
#             right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

#             # Find intersections
#             left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
#             right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)

#             # Optional: draw yellow intersection
#             # Draw thin outline around left intersection
#             contours_left, _ = cv2.findContours(left_intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             cv2.drawContours(frame, contours_left, -1, (0, 255, 255), 1)  # Yellow outline, thickness=1
            
#             for cnt in contours_left:
#                 M = cv2.moments(cnt)
#                 if M["m00"] != 0:
#                     cx = int(M["m10"] / M["m00"])
#                     cy = int(M["m01"] / M["m00"])
#                     cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)  # Red centroid
#                     cv2.putText(frame, "L-C", (cx + 5, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)


#             # Draw thin outline around right intersection
#             contours_right, _ = cv2.findContours(right_intersection, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             cv2.drawContours(frame, contours_right, -1, (0, 255, 255), 1)  # Yellow outline, thickness=1
            
                        
#             for cnt in contours_right:
#                 M = cv2.moments(cnt)
#                 if M["m00"] != 0:
#                     cx = int(M["m10"] / M["m00"])
#                     cy = int(M["m01"] / M["m00"])
#                     cv2.circle(frame, (cx, cy), 3, (255, 0, 0), -1)  # Blue centroid
#                     cv2.putText(frame, "R-C", (cx + 5, cy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

#             # Compute intersection area (can be printed if needed)
#             left_area = cv2.countNonZero(left_intersection)
#             right_area = cv2.countNonZero(right_intersection)

#             # Display ratio or area if needed
#             cv2.putText(frame, f"L:{left_area} R:{right_area}", (30, 40),
#                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

#     cv2.imshow("Iris-Eye Intersection", frame)
#     if cv2.waitKey(1) & 0xFF == 27:  # Press Esc to exit
#         break

# cap.release()
# cv2.destroyAllWindows()






import cv2
import numpy as np
import mediapipe as mp

# Landmark indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

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

# Webcam capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    left_gaze_vector = right_gaze_vector = None
    left_iris_center = right_iris_center = None

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Pixel coordinates
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            # Masks
            left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
            right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
            left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
            right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

            # Intersection
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

                    # Estimate gaze direction using inner/outer landmarks
                    inner = np.array([int(face_landmarks.landmark[eye_landmarks[0]].x * w),
                                    int(face_landmarks.landmark[eye_landmarks[0]].y * h)])
                    outer = np.array([int(face_landmarks.landmark[eye_landmarks[8]].x * w),
                                    int(face_landmarks.landmark[eye_landmarks[8]].y * h)])
                    eye_mid = (inner + outer) // 2
                    cv2.circle(frame, eye_mid, 3, (0, 255, 255), -1)

                    # Gaze vector
                    gaze_vector = (eye_mid - np.array([cx, cy])) * -1
                    gaze_endpoint = (int(cx + gaze_vector[0] * 2.5), int(cy + gaze_vector[1] * 2.5))
                    cv2.arrowedLine(frame, (cx, cy), gaze_endpoint, color, 2, tipLength=0.2)

                    if label == "L-C":
                        return (gaze_vector, (cx, cy))
                    else:
                        return (gaze_vector, (cx, cy))
                return None, None


            left_gaze_vector, left_iris_center = process_eye(left_intersection, LEFT_EYE, (0, 0, 255), "L-C")
            right_gaze_vector, right_iris_center = process_eye(right_intersection, RIGHT_EYE, (255, 0, 0), "R-C")

            # Display area (optional)
            left_area = cv2.countNonZero(left_intersection)
            right_area = cv2.countNonZero(right_intersection)
            cv2.putText(frame, f"L:{left_area} R:{right_area}", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Gaze vector comparison
    if left_gaze_vector is not None and right_gaze_vector is not None:
        # Converging, diverging, or parallel
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
            left_gaze_point = np.array(left_iris_center, dtype=np.float32) + (-left_unit * 40)
            right_gaze_point = np.array(right_iris_center, dtype=np.float32) + (-right_unit * 40)

            original_dist = np.linalg.norm(np.array(left_iris_center) - np.array(right_iris_center))
            shifted_dist = np.linalg.norm(left_gaze_point - right_gaze_point)

            if shifted_dist > original_dist:
                refined_alignment = f"Diverging ({shifted_dist - original_dist:.2f}px)"
            elif shifted_dist < original_dist:
                refined_alignment = f"Converging ({original_dist - shifted_dist:.2f}px)"
            else:
                refined_alignment = "Parallel"

            cv2.putText(frame, f"Refined: {refined_alignment}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2)

    # Show frame
    cv2.imshow("Gaze Vector from Iris-Eye Intersection", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
