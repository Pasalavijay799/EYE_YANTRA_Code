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
            # ==== Iris Center Calculation ====
            def get_iris_center(indices):
                coords = []
                for idx in indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    coords.append((x, y))
                center_x = int(np.mean([p[0] for p in coords]))
                center_y = int(np.mean([p[1] for p in coords]))
                return center_x, center_y

            def landmark_xy(idx):
                lm = face_landmarks.landmark[idx]
                return int(lm.x * w), int(lm.y * h)

            def draw_distance_text(p1, p2, label):
                dist = np.linalg.norm(np.array(p1) - np.array(p2))
                mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
                cv2.line(frame, p1, p2, (255, 255, 0), 1)
                cv2.putText(frame, f"{label}: {dist:.1f}px", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

            # === Right Eye ===
            right_center = get_iris_center(RIGHT_IRIS)
            R_lat = landmark_xy(33)
            R_med = landmark_xy(133)
            R_top = landmark_xy(159)
            R_bot = landmark_xy(145)

            # Draw distances from iris center
            #draw_distance_text(right_center, R_lat, "R_Lateral")
            #draw_distance_text(right_center, R_med, "R_Medial")
            #draw_distance_text(right_center, R_top, "R_Upper")
            draw_distance_text(right_center, R_bot, "R_Lower")

            # === Left Eye ===
            left_center = get_iris_center(LEFT_IRIS)
            L_lat = landmark_xy(263)
            L_med = landmark_xy(362)
            L_top = landmark_xy(386)
            L_bot = landmark_xy(374)

            draw_distance_text(left_center, L_lat, "L_Lateral")
            #draw_distance_text(left_center, L_med, "L_Medial")
            #draw_distance_text(left_center, L_top, "L_Upper")
            #draw_distance_text(left_center, L_bot, "L_Lower")

            # Optionally draw the eye contours (as in your code)
            for eye_landmarks, label in zip([LEFT_EYE, RIGHT_EYE], ['LEFT EYE', 'RIGHT EYE']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

    # Show result
    cv2.imshow('Eye Distances from Iris Center', frame)
    if cv2.waitKey(1) & 0xFF == 27:
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
LEFT_EYE  = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Webcam capture
cap = cv2.VideoCapture(0)

# Function to calculate distance
def compute_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


# === Draw Circles around Irises ===
def draw_iris_circle(iris_indices, center, color):
    iris_coords = []
    for idx in iris_indices:
        x = int(face_landmarks.landmark[idx].x * w)
        y = int(face_landmarks.landmark[idx].y * h)
        iris_coords.append((x, y))

    # Estimate radius as average distance from center to each iris landmark
    radius = int(np.mean([compute_distance(center, pt) for pt in iris_coords]))
    cv2.circle(frame, center, radius, color, 1)  # Draw iris circle
    return(radius)




def draw_eye_circle(eye_indices, color, label):
    eye_coords = []
    for idx in eye_indices:
        x = int(face_landmarks.landmark[idx].x * w)
        y = int(face_landmarks.landmark[idx].y * h)
        eye_coords.append((x, y))

    # Compute center of eye
    center_x = int(np.mean([p[0] for p in eye_coords]))
    center_y = int(np.mean([p[1] for p in eye_coords]))
    center = (center_x, center_y)

    # Estimate radius as mean distance from center
    radius = int(np.mean([compute_distance(center, pt) for pt in eye_coords]))

    # Draw the circle
    cv2.circle(frame, center, radius, color, 1)
    cv2.putText(frame, f"{label} Eye", (center_x - 20, center_y - radius - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)



# Function to draw line, label, return and store distance
def draw_distance(p1, p2, label, frame, distances_dict=None):
    dist = compute_distance(p1, p2)
    mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
    #cv2.line(frame, p1, p2, (255, 255, 0), 1)
    #cv2.putText(frame, f"{label}: {dist:.1f}px", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
    if distances_dict is not None:
        distances_dict[label] = dist
    return dist

def get_eye_center(eye_indices):
    coords = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in eye_indices]
    center_x = int(np.mean([pt[0] for pt in coords]))
    center_y = int(np.mean([pt[1] for pt in coords]))
    return (center_x, center_y)



while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = frame.shape
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            def get_iris_center(indices):
                coords = []
                for idx in indices:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    coords.append((x, y))
                center_x = int(np.mean([p[0] for p in coords]))
                center_y = int(np.mean([p[1] for p in coords]))
                return center_x, center_y

            def landmark_xy(idx):
                lm = face_landmarks.landmark[idx]
                return int(lm.x * w), int(lm.y * h)

            # === Eye Centers ===
            right_center = get_iris_center(RIGHT_IRIS)
            left_center = get_iris_center(LEFT_IRIS)
            left_eye_center = get_eye_center(LEFT_EYE)
            right_eye_center = get_eye_center(RIGHT_EYE)

            cv2.circle(frame, left_eye_center, 2, (255, 0, 255), -1)  # Magenta dot
            cv2.circle(frame, right_eye_center, 2, (255, 0, 255), -1)  # Magenta dot

            cv2.circle(frame, left_center, 2, (255, 0, 255), -1)  # Magenta dot
            cv2.circle(frame, right_center, 2, (255, 0, 255), -1)  # Magenta dot

            # Iris Circles
            L_iris_rad=draw_iris_circle(LEFT_IRIS, left_center, (0, 255, 0))   # Green
            R_iris_rad=draw_iris_circle(RIGHT_IRIS, right_center, (255, 0, 0)) # Blue


            # === Key landmarks ===
            R_lat = landmark_xy(33)
            R_med = landmark_xy(133)
            R_top = landmark_xy(159)
            R_bot = landmark_xy(145)

            L_lat = landmark_xy(263)
            L_med = landmark_xy(362)
            L_top = landmark_xy(386)
            L_bot = landmark_xy(374)

            # Store distances here
            distances = {}

            # Right Eye distances
            # Right Eye distances
            RLD = draw_distance(right_center, R_lat, "R_Lateral", frame, distances)
            RM = draw_distance(right_center, R_med, "R_Medial", frame, distances)
            RUD = draw_distance(right_center, R_top, "R_Upper", frame, distances)
            RLDW = draw_distance(right_center, R_bot, "R_Lower", frame, distances)  # renamed to avoid name clash with RLD above

            # Left Eye distances
            LLD = draw_distance(left_center, L_lat, "L_Lateral", frame, distances)
            LM = draw_distance(left_center, L_med, "L_Medial", frame, distances)
            #cv2.line(frame, left_center, L_med, (255, 255, 0), 1)
            LUD = draw_distance(left_center, L_top, "L_Upper", frame, distances)
            LLDW = draw_distance(left_center, L_bot, "L_Lower", frame, distances)


            # Optionally draw eye contours
            for eye_landmarks, eye_label in zip([LEFT_EYE, RIGHT_EYE], ['Left Eye', 'Right Eye']):
                points = []
                for idx in eye_landmarks:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    points.append((x, y))
                cv2.polylines(frame, [np.array(points, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)
                # Draw bounding rectangle
                x, y, bw, bh = cv2.boundingRect(np.array(points))
                #cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 0, 255), 1)
                cv2.putText(frame, eye_label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                # Calculate center of the bounding rectangle
                center_x = x + bw // 2
                center_y = y + bh // 2
                center_pt = (center_x, center_y)

                # Draw center point
                #cv2.circle(frame, (center_x, center_y), 2, (255, 0, 255), -1)  # Magenta dot

                # Calculate and draw distances to lateral and medial points
                if eye_label == 'Right Eye':

                    # Draw distances
                    CRLD = draw_distance(right_eye_center, R_lat, "R_Center_Lat", frame)
                    CRLD_seg = CRLD / 4
                    # Grading Right Eye lateral deviation
                    grade = -1  # default
                    if RLD > 0.1:
                        if RLD-R_iris_rad < CRLD_seg / 2:
                            grade = 0
                        elif RLD-R_iris_rad< 3 * CRLD_seg / 2:
                            grade = 1
                        elif RLD-R_iris_rad < 5 * CRLD_seg / 2:
                            grade = 2
                        elif RLD-R_iris_rad < 7 * CRLD_seg / 2:
                            grade = 3
                        else:
                            grade = 4

                        # Show grade on frame
                        cv2.putText(frame, f"R_Grade: {grade}", (center_pt[0] + 10, center_pt[1] + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

                    CRMD= draw_distance(center_pt, R_med, "R_Center_Med", frame)
                    #print(CRLD)

                elif eye_label == 'Left Eye':
                    # Draw distances
                    CLLD= draw_distance(left_eye_center, L_lat, "L_Center_Lat", frame)
                    CLMD= draw_distance(left_eye_center, L_med, "L_Center_Med", frame)
                    CLMD_seg = CLMD / 4
                    # Grading Right Eye lateral deviation
                    grade = -1  # default
                    print(LM/CLLD)
                    if LM > 0.1:
                        if LM-L_iris_rad< CLMD_seg / 2:
                            grade = 0
                        elif LM-L_iris_rad < 3 * CLMD_seg / 2:
                            grade = 1
                        elif LM -L_iris_rad< 5 * CLMD_seg / 2:
                            grade = 2
                        elif LM < 7 * CLMD_seg / 2:
                            grade = 3
                        else:
                            grade = 4

                        # Show grade on frame
                        cv2.putText(frame, f"L_Grade: {grade}", (center_pt[0] + 10, center_pt[1] + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Print distances to console
            #print(distances)

    # Show the result
    cv2.imshow('Eye Distances from Iris Center', frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()

