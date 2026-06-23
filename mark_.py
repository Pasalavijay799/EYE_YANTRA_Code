'''
import cv2
import mediapipe as mp
import numpy as np
# Initialize MediaPipe Face Mesh and drawing utilities
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
mp_drawing = mp.solutions.drawing_utils

# Landmark indices for eyes and iris
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Open webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip and convert color
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get face landmarks
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape

            # Draw eye outlines
            for eye_landmarks in [LEFT_EYE, RIGHT_EYE]:
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

            # Draw iris centers
            for iris_indices, color in zip([LEFT_IRIS, RIGHT_IRIS], [(255, 0, 0), (0, 0, 255)]):
                iris_points = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_points.append((x, y))
                    cv2.circle(frame, (x, y), 1, color, -1)

    # Display the frame
    cv2.imshow('Eye Tracking', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
'''


'''
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
mp_drawing = mp.solutions.drawing_utils

# Correct landmark indices for eyes and irises
LEFT_EYE  = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    #frame = cv2.flip(frame, 1)  # Mirror the image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Draw eye outlines and labels
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                # Draw eye contour
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

                # Eye label
                eye_ref_point = face_landmarks.landmark[eye_landmarks[0]]
                label_x = int(eye_ref_point.x * w)
                label_y = int(eye_ref_point.y * h) - 10
                cv2.putText(frame, label, (label_x - 40, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Draw iris points, centers, and label
            for iris_indices, iris_label, color in zip(
                [LEFT_IRIS, RIGHT_IRIS],
                ['LEFT IRIS', 'RIGHT IRIS'],
                [(255, 0, 0), (0, 0, 255)]
            ):
                iris_coords = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_coords.append((x, y))
                    cv2.circle(frame, (x, y), 1, color, -1)

                # Draw iris center
                if iris_coords:
                    center_x = int(np.mean([p[0] for p in iris_coords]))
                    center_y = int(np.mean([p[1] for p in iris_coords]))
                    cv2.circle(frame, (center_x, center_y), 2, color, -1)
                    # Iris label
                    cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Show the result
    cv2.imshow('Eye & Iris Tracking', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()

'''
'''
#best
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

# Landmark indices
LEFT_EYE  = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Draw eye outlines and labels
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

                # Eye label
                ref_point = face_landmarks.landmark[eye_landmarks[0]]
                label_x = int(ref_point.x * w)
                label_y = int(ref_point.y * h) - 10
                cv2.putText(frame, label, (label_x - 40, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Draw iris points, centers, and labels
            for iris_indices, iris_label, color in zip(
                [LEFT_IRIS, RIGHT_IRIS],
                ['LEFT IRIS', 'RIGHT IRIS'],
                [(255, 0, 0), (0, 0, 255)]
            ):
                iris_coords = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_coords.append((x, y))
                    cv2.circle(frame, (x, y), 1, color, -1)

                if iris_coords:
                    center_x = int(np.mean([p[0] for p in iris_coords]))
                    center_y = int(np.mean([p[1] for p in iris_coords]))
                    cv2.circle(frame, (center_x, center_y), 2, color, -1)
                    cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # === Individually Highlight Key Eye Points ===
            # Right Lateral Canthus
            pt = face_landmarks.landmark[33]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "R_Lateral_Canthus", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Right Medial Canthus
            pt = face_landmarks.landmark[133]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "R_Medial_Canthus", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Left Lateral Canthus
            pt = face_landmarks.landmark[263]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "L_Lateral_Canthus", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Left Medial Canthus
            pt = face_landmarks.landmark[362]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "L_Medial_Canthus", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Right Upper Lid
            pt = face_landmarks.landmark[159]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "R_Upper_Lid", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Right Lower Lid
            pt = face_landmarks.landmark[145]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            cv2.putText(frame, "R_Lower_Lid", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Left Upper Lid
            pt = face_landmarks.landmark[386]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            cv2.putText(frame, "L_Upper_Lid", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            # Left Lower Lid
            pt = face_landmarks.landmark[374]
            x, y = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
            #cv2.putText(frame, "L_Lower_Lid", (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

    # Show the result
    cv2.imshow('Eye & Iris Tracking with Individual Labels', frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
'''






'''
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

# Landmark indices
LEFT_EYE  = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Draw eye outlines and labels
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

                # Eye label
                ref_point = face_landmarks.landmark[eye_landmarks[0]]
                label_x = int(ref_point.x * w)
                label_y = int(ref_point.y * h) - 10
                cv2.putText(frame, label, (label_x - 40, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Draw iris circles and direction vectors
            for iris_indices, iris_label, color in zip(
                [LEFT_IRIS, RIGHT_IRIS],
                ['LEFT IRIS', 'RIGHT IRIS'],
                [(255, 0, 0), (0, 0, 255)]
            ):
                iris_coords = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_coords.append((x, y))
                    #cv2.circle(frame, (x, y), 1, color, -1)

                if iris_coords:
                    # Calculate min enclosing circle
                    center, radius = cv2.minEnclosingCircle(np.array(iris_coords, dtype=np.int32))
                    center = (int(center[0]), int(center[1]))
                    radius = int(radius)
                    #cv2.circle(frame, center, radius, color, 1)
                    #cv2.putText(frame, iris_label, (center[0] - 30, center[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                    # Estimate direction vector (simplified)
                    if iris_label == 'RIGHT IRIS':
                        lateral_idx = 33
                        medial_idx = 133
                    else:
                        lateral_idx = 263
                        medial_idx = 362

                    lateral = face_landmarks.landmark[lateral_idx]
                    medial = face_landmarks.landmark[medial_idx]
                    eye_vec = np.array([
                        (medial.x - lateral.x) * w,
                        (medial.y - lateral.y) * h
                    ])
                    perp_vec = np.array([-eye_vec[1], eye_vec[0]])
                    perp_vec = perp_vec / np.linalg.norm(perp_vec) * 40  # Scale for visibility

                    pt1 = center
                    pt2 = (int(center[0] + perp_vec[0]), int(center[1] + perp_vec[1]))
                    cv2.arrowedLine(frame, pt1, pt2, color, 2, tipLength=0.2)

            # Highlight key points around the eyes
            highlight_indices = {
                'R_Lateral_Canthus': 33,
                'R_Medial_Canthus': 133,
                'L_Lateral_Canthus': 263,
                'L_Medial_Canthus': 362,
                'R_Upper_Lid': 159,
                'R_Lower_Lid': 145,
                'L_Upper_Lid': 386,
                'L_Lower_Lid': 374
            }
            for label, idx in highlight_indices.items():
                pt = face_landmarks.landmark[idx]
                x, y = int(pt.x * w), int(pt.y * h)
                cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)
                if 'Lower' in label or 'Upper' in label:
                    cv2.putText(frame, label, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

    # Display the output
    cv2.imshow('Eye & Iris Tracking with Direction Vectors', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()




'''





'''
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

# Landmark indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

            # Draw iris circle and gaze vector
            for iris_indices, iris_label, eye_landmarks, color in zip(
                [LEFT_IRIS, RIGHT_IRIS],
                ['LEFT IRIS', 'RIGHT IRIS'],
                [LEFT_EYE, RIGHT_EYE],
                [(255, 0, 0), (0, 0, 255)]
            ):
                iris_coords = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_coords.append((x, y))
                    cv2.circle(frame, (x, y), 1, color, -1)

                if iris_coords:
                    center_x = int(np.mean([p[0] for p in iris_coords]))
                    center_y = int(np.mean([p[1] for p in iris_coords]))

                    # Fit a circle to the iris (approximate)
                    (iris_center, radius) = cv2.minEnclosingCircle(np.array(iris_coords))
                    iris_center = (int(iris_center[0]), int(iris_center[1]))
                    radius = int(radius)
                    cv2.circle(frame, iris_center, radius, color, 1)

                    # Estimate gaze direction (from iris center to midpoint of eye corners)
                    inner_corner = face_landmarks.landmark[eye_landmarks[0]]
                    outer_corner = face_landmarks.landmark[eye_landmarks[8]]
                    inner = np.array([int(inner_corner.x * w), int(inner_corner.y * h)])
                    outer = np.array([int(outer_corner.x * w), int(outer_corner.y * h)])
                    eye_mid = (inner + outer) // 2

                    gaze_vector = (eye_mid - np.array([center_x, center_y])) * -1  # Invert to simulate gaze
                    gaze_endpoint = (int(center_x + gaze_vector[0] * 6), int(center_y + gaze_vector[1] * 6))

                    cv2.arrowedLine(frame, (center_x, center_y), gaze_endpoint, color, 2, tipLength=0.2)
                    cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    left_gaze_vector = None
                    right_gaze_vector = None
                    if iris_label == 'LEFT IRIS':
                        left_gaze_vector = gaze_vector
                    elif iris_label == 'RIGHT IRIS':
                        right_gaze_vector = gaze_vector
    if left_gaze_vector is not None and right_gaze_vector is not None:
        # Normalize vectors
        a = left_gaze_vector.astype(np.float32)
        b = right_gaze_vector.astype(np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a > 0 and norm_b > 0:
            cos_theta = np.dot(a, b) / (norm_a * norm_b)
            cos_theta = np.clip(cos_theta, -1.0, 1.0)  # Prevent numerical errors
            angle_deg = np.degrees(np.arccos(cos_theta))

            # Display angle
            cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Optional: Determine if nearly parallel
            if angle_deg < 15 or angle_deg > 165:
                status = "Parallel"
            else:
                status = "Not Parallel"

            cv2.putText(frame, f"Status: {status}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)



    # Show the result
    cv2.imshow('Eye & Iris Tracking with Gaze Vectors', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
'''
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

# Landmark indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

cap = cv2.VideoCapture(0)

# Initialize gaze vectors outside the loop to track both eyes' vectors
left_gaze_vector = None
right_gaze_vector = None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

            # Draw iris circle and gaze vector
            for iris_indices, iris_label, eye_landmarks, color in zip(
                [LEFT_IRIS, RIGHT_IRIS],
                ['LEFT IRIS', 'RIGHT IRIS'],
                [LEFT_EYE, RIGHT_EYE],
                [(255, 0, 0), (0, 0, 255)]
            ):
                iris_coords = []
                for idx in iris_indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    iris_coords.append((x, y))
                    cv2.circle(frame, (x, y), 1, color, -1)

                if iris_coords:
                    center_x = int(np.mean([p[0] for p in iris_coords]))
                    center_y = int(np.mean([p[1] for p in iris_coords]))

                    # Fit a circle to the iris (approximate)
                    (iris_center, radius) = cv2.minEnclosingCircle(np.array(iris_coords))
                    iris_center = (int(iris_center[0]), int(iris_center[1]))
                    radius = int(radius)
                    cv2.circle(frame, iris_center, radius, color, 1)

                    # Estimate gaze direction (from iris center to midpoint of eye corners)
                    inner_corner = face_landmarks.landmark[eye_landmarks[0]]
                    outer_corner = face_landmarks.landmark[eye_landmarks[8]]
                    inner = np.array([int(inner_corner.x * w), int(inner_corner.y * h)])
                    outer = np.array([int(outer_corner.x * w), int(outer_corner.y * h)])
                    eye_mid = (inner + outer) // 2
                    cv2.circle(frame, eye_mid, 3, (0, 255, 255), -1)

                    gaze_vector = (eye_mid - np.array([center_x, center_y])) * -1  # Invert to simulate gaze
                    gaze_endpoint = (int(center_x + gaze_vector[0] * 6), int(center_y + gaze_vector[1] * 6))

                    cv2.arrowedLine(frame, (center_x, center_y), gaze_endpoint, color, 2, tipLength=0.2)
                    cv2.putText(frame, iris_label, (center_x - 30, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                    # Store gaze vectors
                    gazevector = (center_x - gaze_endpoint[0], center_y - gaze_endpoint[1])
                    if iris_label == 'LEFT IRIS':
                        left_gaze_vector = gazevector
                    elif iris_label == 'RIGHT IRIS':
                        right_gaze_vector = gazevector

    # Calculate the angle only when both gaze vectors are available
    if left_gaze_vector is not None and right_gaze_vector is not None:
        # Normalize vectors
        # Compare horizontal (x) direction of vectors
        left_dx = left_gaze_vector[0]
        right_dx = right_gaze_vector[0]
        cv2.putText(frame, f"rightdx: {right_dx}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 100), 2)
        cv2.putText(frame, f"lefttdx: {left_dx}", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 100), 2)

        if left_dx > 0 and right_dx < 0:
            eye_alignment = "Converging"
        elif left_dx < 0 and right_dx > 0:
            eye_alignment = "Diverging"
        else:
            eye_alignment = "Parallel/Undetermined"

        # Show on frame
        cv2.putText(frame, f"Eye Alignment: {eye_alignment}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 100), 2)
        a = np.array(left_gaze_vector, dtype=np.float32)
        b = np.array(right_gaze_vector, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a > 0 and norm_b > 0:
            cos_theta = np.dot(a, b) / (norm_a * norm_b)
            cos_theta = np.clip(cos_theta, -1.0, 1.0)  # Prevent numerical errors
            angle_deg = np.degrees(np.arccos(cos_theta))

            # Display angle
            cv2.putText(frame, f"Gaze Angle: {angle_deg:.1f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Optional: Determine if nearly parallel
            if angle_deg < 30 or angle_deg > 150:
                status = "Parallel"
            else:
                status = "Not Parallel"

            cv2.putText(frame, f"Status: {status}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Show the result
    cv2.imshow('Eye & Iris Tracking with Gaze Vectors', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
