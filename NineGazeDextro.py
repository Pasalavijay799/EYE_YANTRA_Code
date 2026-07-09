import cv2
import mediapipe as mp
import numpy as np

class EyeAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

    def compute_distance(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def get_center(self, indices, landmarks, w, h):
        coords = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices]
        center_x = int(np.mean([pt[0] for pt in coords]))
        center_y = int(np.mean([pt[1] for pt in coords]))
        return (center_x, center_y)

    def draw_circle(self, indices, center, color, frame, landmarks, w, h):
        iris_coords = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices]
        radius = int(np.mean([self.compute_distance(center, pt) for pt in iris_coords]))
        cv2.circle(frame, center, radius, color, 1)
        return radius

    def get_landmark_xy(self, idx, landmarks, w, h):
        lm = landmarks[idx]
        return int(lm.x * w), int(lm.y * h)

    def draw_distance(self, p1, p2, label, frame, distances_dict=None):
        dist = self.compute_distance(p1, p2)
        if distances_dict is not None:
            distances_dict[label] = dist
        return dist

    def process_frame(self, frame,gaze_direction="center"):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        results = self.face_mesh.process(rgb)

        output = {
            "distances": {},
            "grades": {},
            "processed_frame": frame.copy()
        }

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                frame = output["processed_frame"]

                # Iris and Eye Centers
                left_iris_center = self.get_center(self.LEFT_IRIS, landmarks, w, h)
                right_iris_center = self.get_center(self.RIGHT_IRIS, landmarks, w, h)
                left_eye_center = self.get_center(self.LEFT_EYE, landmarks, w, h)
                right_eye_center = self.get_center(self.RIGHT_EYE, landmarks, w, h)

                # Draw centers
                for center in [left_eye_center, right_eye_center, left_iris_center, right_iris_center]:
                    cv2.circle(frame, center, 2, (255, 0, 255), -1)

                # Iris radius
                L_iris_rad = self.draw_circle(self.LEFT_IRIS, left_iris_center, (0, 255, 0), frame, landmarks, w, h)
                R_iris_rad = self.draw_circle(self.RIGHT_IRIS, right_iris_center, (255, 0, 0), frame, landmarks, w, h)

                # Get key landmarks
                L_med = self.get_landmark_xy(362, landmarks, w, h)
                L_lat = self.get_landmark_xy(263, landmarks, w, h)
                L_top = self.get_landmark_xy(386, landmarks, w, h)
                L_bot = self.get_landmark_xy(374, landmarks, w, h)

                R_med = self.get_landmark_xy(133, landmarks, w, h)
                R_lat = self.get_landmark_xy(33, landmarks, w, h)
                R_top = self.get_landmark_xy(159, landmarks, w, h)
                R_bot = self.get_landmark_xy(145, landmarks, w, h)

                distances = output["distances"]

                # Right Eye distances
                RLD = self.draw_distance(right_iris_center, R_lat, "R_Lateral", frame, distances)
                RM = self.draw_distance(right_iris_center, R_med, "R_Medial", frame, distances)
                RUD = self.draw_distance(right_iris_center, R_top, "R_Upper", frame, distances)
                RLDW = self.draw_distance(right_iris_center, R_bot, "R_Lower", frame, distances)

                # Left Eye distances
                LLD = self.draw_distance(left_iris_center, L_lat, "L_Lateral", frame, distances)
                LM = self.draw_distance(left_iris_center, L_med, "L_Medial", frame, distances)
                LUD = self.draw_distance(left_iris_center, L_top, "L_Upper", frame, distances)
                LLDW = self.draw_distance(left_iris_center, L_bot, "L_Lower", frame, distances)

                # === DEXTROVERSION CASE (Looking Right) ===
                if gaze_direction == "dextro":
                    # Grade Right Lateral
                    CRLD = self.compute_distance(right_eye_center, R_lat)
                    CRLD_seg = CRLD / 4
                    grade_r = -1
                    if RLD > 0.1:
                        if RLD - R_iris_rad < CRLD_seg / 2:
                            grade_r = 0
                        elif RLD  - R_iris_rad< 3 * CRLD_seg / 2:
                            grade_r = -1
                        elif RLD - R_iris_rad < 5 * CRLD_seg / 2:
                            grade_r = -2
                        elif RLD - R_iris_rad < 7 * CRLD_seg / 2:
                            grade_r = -3
                        else:
                            grade_r = -4
                    output["grades"]["R_Lateral"] = grade_r
                    # cv2.putText(frame, f"R_Lat Grade: {grade_r}", (right_iris_center[0] + 10, right_iris_center[1] + 20),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    #testing
                    cv2.putText(frame, f"Grade: {grade_r}", (right_iris_center[0]-50, right_iris_center[1] + 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    cv2.putText(frame, "R_Lat", (right_iris_center[0]-50, right_iris_center[1] + 55),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

                    # Grade Left Medial
                    CLMD = self.compute_distance(left_eye_center, L_med)
                    CLMD_seg = CLMD / 4
                    grade_medial = -1
                    if LM > 0.1:
                        if LM - L_iris_rad < CLMD_seg / 2:
                            grade_medial = 0
                        elif LM - L_iris_rad < 3 * CLMD_seg / 2:
                            grade_medial = -1
                        elif LM - L_iris_rad < 5 * CLMD_seg / 2:
                            grade_medial = -2
                        elif LM - L_iris_rad < 7 * CLMD_seg / 2:
                            grade_medial = -3
                        else:
                            grade_medial = -4
                    output["grades"]["L_Medial"] = grade_medial
                    # cv2.putText(frame, f"L_Med Grade: {grade_medial}", (left_iris_center[0] + 10, left_iris_center[1] + 40),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    #testing
                    cv2.putText(frame, f"Grade: {grade_medial}", (left_iris_center[0] - 30, left_iris_center[1] + 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    cv2.putText(frame, "L _ Med", (left_iris_center[0], left_iris_center[1] + 55),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                # === LEVOVERSION CASE (Looking Left) ===
                elif gaze_direction == "levo":
                    # Grade Left Lateral
                    CLLD = self.compute_distance(left_eye_center, L_lat)
                    CLLD_seg = CLLD / 4
                    grade_l = -1
                    if LLD > 0.1:
                        if LLD - L_iris_rad < CLLD_seg / 2:
                            grade_l = 0
                        elif LLD - L_iris_rad < 3 * CLLD_seg / 2:
                            grade_l = -1
                        elif LLD - L_iris_rad < 5 * CLLD_seg / 2:
                            grade_l = -2
                        elif LLD - L_iris_rad < 7 * CLLD_seg / 2:
                            grade_l = -3
                        else:
                            grade_l = -4
                    output["grades"]["L_Lateral"] = grade_l
                    # cv2.putText(frame, f"L_Lat Grade: {grade_l}", (left_iris_center[0] + 10, left_iris_center[1] + 20),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    #testing
                    cv2.putText(frame, f"Grade: {grade_l}", (left_iris_center[0] - 30, left_iris_center[1] + 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255,255), 1)
                    cv2.putText(frame, "L _ Lat", (left_iris_center[0], left_iris_center[1] + 55),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

                    # Grade Right Medial
                    CRMD = self.compute_distance(right_eye_center, R_med)
                    CRMD_seg = CRMD / 4
                    grade_r_medial = -1
                    if RM > 0.1:
                        if RM - R_iris_rad < CRMD_seg / 2:
                            grade_r_medial = 0
                        elif RM - R_iris_rad < 3 * CRMD_seg / 2:
                            grade_r_medial = -1
                        elif RM - R_iris_rad < 5 * CRMD_seg / 2:
                            grade_r_medial = -2
                        elif RM - R_iris_rad < 7 * CRMD_seg / 2:
                            grade_r_medial = -3
                        else:
                            grade_r_medial = -4
                    output["grades"]["R_Medial"] = grade_r_medial
                    # cv2.putText(frame, f"R_Med Grade: {grade_r_medial}", (right_iris_center[0] + 10, right_iris_center[1] + 40),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    #testing
                    cv2.putText(frame, f"Grade: {grade_r_medial}", (right_iris_center[0] - 50, right_iris_center[1] + 40),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    cv2.putText(frame, "R_Med", (right_iris_center[0] - 50, right_iris_center[1] + 55),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)


        return output
