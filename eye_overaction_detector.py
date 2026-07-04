import cv2
import mediapipe as mp
import numpy as np
import math


class EyeIrisDetector:
    def __init__(self, mode='both'):
        self.mode = mode  # 'left', 'right', or 'both'

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

        # Landmark indices
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

    def vector_angle(self, v1, v2):
        dot = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        cos_angle = dot / (norm_v1 * norm_v2 + 1e-6)
        angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return math.degrees(angle_rad)

    def grade_overaction(self, angle):
        if angle <= 15:
            return 1
        elif angle <= 30:
            return 2
        elif angle <= 60:
            return 3
        elif angle <= 90:
            return 4
        else:
            return 4

    def draw_eye_analysis(self, image, landmarks, image_w, image_h):
        def to_pixel(landmark):
            return int(landmark.x * image_w), int(landmark.y * image_h)

        def get_points(indices):
            return np.array([to_pixel(landmarks[i]) for i in indices])

        eye_centers = {}
        iris_centers = {}
        anchor_points = {}

        eyes = []
        if self.mode in ['left', 'both']:
            eyes.append('left')
        if self.mode in ['right', 'both']:
            eyes.append('right')

        for label in eyes:
            eye_indices = self.LEFT_EYE if label == 'left' else self.RIGHT_EYE
            iris_indices = self.LEFT_IRIS if label == 'left' else self.RIGHT_IRIS

            points = get_points(eye_indices)
            x, y, w, h = cv2.boundingRect(points)
            eye_center = (x + w // 2, y + h // 2)
            anchor = (x + w, y + h // 2) if label == 'left' else (x, y + h // 2)

            eye_centers[label] = eye_center
            anchor_points[label] = anchor

            # Draw bounding box and label
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, "L" if label == "left" else "R", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Iris center and radius
            iris_pts = get_points(iris_indices)
            iris_center = np.mean(iris_pts, axis=0).astype(int)
            iris_centers[label] = tuple(iris_center)
            radius = int(np.linalg.norm(iris_pts[0] - iris_center))
            cv2.circle(image, tuple(iris_center), radius, (0, 0, 255), 2)

            # Draw lines
            cv2.line(image, anchor, eye_center, (255, 0, 0), 2)  # Blue
            cv2.line(image, iris_center, eye_center, (0, 255, 255), 2)  # Yellow

            # Compute angle and grade
            vec1 = np.array(eye_center) - np.array(anchor)
            vec2 = np.array(eye_center) - np.array(iris_center)
            angle = self.vector_angle(vec1, vec2)
            grade = self.grade_overaction(angle)

            # Annotate
            offset = 30 if label == 'left' else 60
            cv2.putText(image, f"{label.capitalize()} angle: {angle:.2f} deg", (30, offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(image, f"{label.capitalize()} Overaction Grade: {grade}", (30, offset + 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    def run_on_image(self, image_path, show=True):
        image = cv2.imread(image_path)
        if image is None:
            print("Failed to load image.")
            return None

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.draw_eye_analysis(image, face_landmarks.landmark, image.shape[1], image.shape[0])
        else:
            print("No face detected.")
            return image

        if show:
            cv2.imshow("Eye Overaction Detection", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return image
