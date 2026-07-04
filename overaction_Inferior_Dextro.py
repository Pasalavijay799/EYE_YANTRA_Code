# import cv2
# import mediapipe as mp
# import numpy as np

# class EyeIrisDetector:
#     def __init__(self):
#         self.mp_face_mesh = mp.solutions.face_mesh
#         self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
#         self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
#         self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
#         self.LEFT_IRIS = [474, 475, 476, 477]
#         self.RIGHT_IRIS = [469, 470, 471, 472]

#     def draw_eye_rect_and_iris_circles(self, image, landmarks, image_w, image_h):
#         # Helper function to get 2D points
#         def get_points(indices):
#             return np.array([(int(landmarks[i].x * image_w), int(landmarks[i].y * image_h)) for i in indices])

#         # Draw eye rectangles
#         for eye_indices in [self.LEFT_EYE, self.RIGHT_EYE]:
#             points = get_points(eye_indices)
#             x, y, w, h = cv2.boundingRect(points)
#             cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

#         # Draw iris circles
#         for iris_indices in [self.LEFT_IRIS, self.RIGHT_IRIS]:
#             iris_points = get_points(iris_indices)
#             center = np.mean(iris_points, axis=0).astype(int)
#             radius = int(np.linalg.norm(iris_points[0] - center))
#             cv2.circle(image, tuple(center), radius, (0, 0, 255), 2)

#     def run(self):
#         cap = cv2.VideoCapture(0)

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = self.face_mesh.process(frame_rgb)

#             if results.multi_face_landmarks:
#                 for face_landmarks in results.multi_face_landmarks:
#                     self.draw_eye_rect_and_iris_circles(frame, face_landmarks.landmark, frame.shape[1], frame.shape[0])

#             cv2.imshow("Eye & Iris Detection", frame)
#             if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
#                 break

#         cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     EyeIrisDetector().run()








# import cv2
# import mediapipe as mp
# import numpy as np

# class EyeIrisDetector:
#     def __init__(self):
#         self.mp_face_mesh = mp.solutions.face_mesh
#         self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
#         self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
#         self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
#         self.LEFT_IRIS = [474, 475, 476, 477]
#         self.RIGHT_IRIS = [469, 470, 471, 472]

#     def draw_eye_rect_and_iris_circles(self, image, landmarks, image_w, image_h):
#         def to_pixel(landmark):
#             return int(landmark.x * image_w), int(landmark.y * image_h)

#         def get_points(indices):
#             return np.array([to_pixel(landmarks[i]) for i in indices])

#         eye_centers = {}
#         # Draw eye rectangles and get centers
#         for label, eye_indices in zip(["left", "right"], [self.LEFT_EYE, self.RIGHT_EYE]):
#             points = get_points(eye_indices)
#             x, y, w, h = cv2.boundingRect(points)
#             center = (x + w // 2, y + h // 2)
#             eye_centers[label] = center
#             cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

#         # Draw iris circles and get centers
#         iris_centers = {}
#         for label, iris_indices in zip(["left", "right"], [self.LEFT_IRIS, self.RIGHT_IRIS]):
#             points = get_points(iris_indices)
#             center = np.mean(points, axis=0).astype(int)
#             iris_centers[label] = tuple(center)
#             radius = int(np.linalg.norm(points[0] - center))
#             cv2.circle(image, tuple(center), radius, (0, 0, 255), 2)

#         # Draw lines from lateral/medial canthus to rectangle centers
#         right_lateral_canthus = to_pixel(landmarks[33])
#         left_medial_canthus = to_pixel(landmarks[362])
#         cv2.line(image, right_lateral_canthus, eye_centers["right"], (255, 0, 0), 2)    # Blue
#         cv2.line(image, left_medial_canthus, eye_centers["left"], (0, 255, 0), 2)       # Green

#         # Draw lines from iris centers to rectangle centers
#         cv2.line(image, iris_centers["right"], eye_centers["right"], (0, 255, 255), 2)  # Yellow
#         cv2.line(image, iris_centers["left"], eye_centers["left"], (255, 0, 255), 2)    # Magenta


#     def run(self):
#         cap = cv2.VideoCapture(0)

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = self.face_mesh.process(frame_rgb)

#             if results.multi_face_landmarks:
#                 for face_landmarks in results.multi_face_landmarks:
#                     self.draw_eye_rect_and_iris_circles(frame, face_landmarks.landmark, frame.shape[1], frame.shape[0])

#             cv2.imshow("Eye & Iris Detection", frame)
#             if cv2.waitKey(1) & 0xFF == 27:  # ESC key
#                 break

#         cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     EyeIrisDetector().run()








#on videostream best
# import cv2
# import mediapipe as mp
# import numpy as np
# import math

# class EyeIrisDetector:
#     def __init__(self):
#         self.mp_face_mesh = mp.solutions.face_mesh
#         self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
#         self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
#         self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
#         self.LEFT_IRIS = [474, 475, 476, 477]
#         self.RIGHT_IRIS = [469, 470, 471, 472]

#     def vector_angle(self, v1, v2):
#         """Compute angle between two vectors in degrees using dot product."""
#         dot = np.dot(v1, v2)
#         norm_v1 = np.linalg.norm(v1)
#         norm_v2 = np.linalg.norm(v2)
#         cos_angle = dot / (norm_v1 * norm_v2 + 1e-6)  # avoid division by zero
#         angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0))
#         return math.degrees(angle_rad)

#     def draw_eye_rect_and_iris_circles(self, image, landmarks, image_w, image_h):
#         def to_pixel(landmark):
#             return int(landmark.x * image_w), int(landmark.y * image_h)

#         def get_points(indices):
#             return np.array([to_pixel(landmarks[i]) for i in indices])

#         eye_centers = {}
#         iris_centers = {}

#         # Draw eye rectangles and store centers
#         for label, eye_indices in zip(["left", "right"], [self.LEFT_EYE, self.RIGHT_EYE]):
#             points = get_points(eye_indices)
#             x, y, w, h = cv2.boundingRect(points)
#             center = (x + w // 2, y + h // 2)
#             eye_centers[label] = center
#             cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

#         # Draw iris circles and store centers
#         for label, iris_indices in zip(["left", "right"], [self.LEFT_IRIS, self.RIGHT_IRIS]):
#             points = get_points(iris_indices)
#             center = np.mean(points, axis=0).astype(int)
#             iris_centers[label] = tuple(center)
#             radius = int(np.linalg.norm(points[0] - center))
#             cv2.circle(image, tuple(center), radius, (0, 0, 255), 2)

#         # Get canthus points
#         right_lateral_canthus = to_pixel(landmarks[33])
#         left_medial_canthus = to_pixel(landmarks[362])

#         # Draw canthus → eye center lines
#         cv2.line(image, right_lateral_canthus, eye_centers["right"], (255, 0, 0), 2)  # Blue
#         cv2.line(image, left_medial_canthus, eye_centers["left"], (0, 255, 0), 2)     # Green

#         # Draw iris center → eye center lines
#         cv2.line(image, iris_centers["right"], eye_centers["right"], (0, 255, 255), 2)  # Yellow
#         cv2.line(image, iris_centers["left"], eye_centers["left"], (255, 0, 255), 2)    # Magenta

#         # Calculate angles using vector math
#         vec_r1 = np.array(eye_centers["right"]) - np.array(right_lateral_canthus)
#         vec_r2 = np.array(eye_centers["right"]) - np.array(iris_centers["right"])
#         right_angle = self.vector_angle(vec_r1, vec_r2)

#         vec_l1 = np.array(eye_centers["left"]) - np.array(left_medial_canthus)
#         vec_l2 = np.array(eye_centers["left"]) - np.array(iris_centers["left"])
#         left_angle = self.vector_angle(vec_l1, vec_l2)

#         # Display angles on image
#         cv2.putText(image, f"Right angle: {right_angle:.2f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
#         cv2.putText(image, f"Left angle: {left_angle:.2f} deg", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

#     def run(self):
#         cap = cv2.VideoCapture(0)

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = self.face_mesh.process(frame_rgb)

#             if results.multi_face_landmarks:
#                 for face_landmarks in results.multi_face_landmarks:
#                     self.draw_eye_rect_and_iris_circles(frame, face_landmarks.landmark, frame.shape[1], frame.shape[0])

#             cv2.imshow("Eye & Iris Detection", frame)
#             if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
#                 break

#         cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     EyeIrisDetector().run()









import cv2
import mediapipe as mp
import numpy as np
import math

class EyeIrisDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
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

    def draw_eye_rect_and_iris_circles(self, image, landmarks, image_w, image_h):
        def to_pixel(landmark):
            return int(landmark.x * image_w), int(landmark.y * image_h)

        def get_points(indices):
            return np.array([to_pixel(landmarks[i]) for i in indices])

        eye_centers = {}
        iris_centers = {}
        anchor_points = {}

        for label, eye_indices in zip(["left", "right"], [self.LEFT_EYE, self.RIGHT_EYE]):
            points = get_points(eye_indices)
            x, y, w, h = cv2.boundingRect(points)
            center = (x + w // 2, y + h // 2)
            eye_centers[label] = center

            # Draw the bounding rectangle
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Set anchor point to left edge midpoint for both eyes
            anchor = (x, y + h // 2)
            anchor_points[label] = anchor

        for label, iris_indices in zip(["left", "right"], [self.LEFT_IRIS, self.RIGHT_IRIS]):
            points = get_points(iris_indices)
            center = np.mean(points, axis=0).astype(int)
            iris_centers[label] = tuple(center)
            radius = int(np.linalg.norm(points[0] - center))
            cv2.circle(image, tuple(center), radius, (0, 0, 255), 2)

        # Draw lines: anchor → eye center (anchor lines)
        cv2.line(image, anchor_points["right"], eye_centers["right"], (255, 0, 0), 2)  # Blue
        cv2.line(image, anchor_points["left"], eye_centers["left"], (0, 255, 0), 2)    # Green

        # Draw lines: iris center → eye center (iris tracking)
        cv2.line(image, iris_centers["right"], eye_centers["right"], (0, 255, 255), 2)  # Yellow
        cv2.line(image, iris_centers["left"], eye_centers["left"], (255, 0, 255), 2)    # Magenta

        # Compute angles
        vec_r1 = np.array(eye_centers["right"]) - np.array(anchor_points["right"])
        vec_r2 = np.array(eye_centers["right"]) - np.array(iris_centers["right"])
        right_angle = self.vector_angle(vec_r1, vec_r2)

        vec_l1 = np.array(eye_centers["left"]) - np.array(anchor_points["left"])
        vec_l2 = np.array(eye_centers["left"]) - np.array(iris_centers["left"])

        left_angle = self.vector_angle(vec_l1, vec_l2)
        left_grade = self.grade_overaction(left_angle)
        right_grade = self.grade_overaction(right_angle)

        # Display grades on image
        cv2.putText(image, f"Left Grade: {left_grade}", (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(image, f"Right Grade: {right_grade}", (30, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Display the angles
        cv2.putText(image, f"Right angle: {right_angle:.2f} deg", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(image, f"Left angle: {left_angle:.2f} deg", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)



    def grade_overaction(self, angle):
        """Grades the overaction severity based on angle thresholds."""
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
    def run_on_image(self, image_path, show=True):
        image = cv2.imread(image_path)
        if image is None:
            print("Failed to load image.")
            return None

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.draw_eye_rect_and_iris_circles(image, face_landmarks.landmark, image.shape[1], image.shape[0])
        else:
            print("No face detected.")
            return image

        if show:
            cv2.imshow("Eye & Iris Detection", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return image


