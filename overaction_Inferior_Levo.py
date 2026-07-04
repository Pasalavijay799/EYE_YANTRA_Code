import cv2
import mediapipe as mp
import numpy as np
import math

class EyeIrisDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

        # Mediapipe landmark indices for eyes and irises
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

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

    def vector_angle(self, v1, v2):
        """Returns the angle (in degrees) between two vectors."""
        dot = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        cos_angle = dot / (norm_v1 * norm_v2 + 1e-6)
        angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        degree=math.degrees(angle_rad)
        # if math.degrees(angle_rad)>90:
        #     degree= 180 -degree

        return degree

    def draw_eye_rect_and_iris_circles(self, image, landmarks, image_w, image_h):
        def to_pixel(landmark):
            return int(landmark.x * image_w), int(landmark.y * image_h)

        def get_points(indices):
            return np.array([to_pixel(landmarks[i]) for i in indices])

        eye_centers = {}
        iris_centers = {}
        anchor_points = {}

        # Process both eyes
        # Process both eyes
        for label, eye_indices in zip(["left", "right"], [self.LEFT_EYE, self.RIGHT_EYE]):
            points = get_points(eye_indices)
            x, y, w, h = cv2.boundingRect(points)
            center = (x + w // 2, y + h // 2)
            eye_centers[label] = center

            # Draw eye bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Label the eyes with "L" or "R" near the bounding box
            label_text = "L" if label == "left" else "R"
            cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)


            # Set anchor to right edge midpoint for both eyes
            anchor = (x + w, y + h // 2)
            anchor_points[label] = anchor


        # Process iris points
        for label, iris_indices in zip(["left", "right"], [self.LEFT_IRIS, self.RIGHT_IRIS]):
            points = get_points(iris_indices)
            center = np.mean(points, axis=0).astype(int)
            iris_centers[label] = tuple(center)
            radius = int(np.linalg.norm(points[0] - center))
            cv2.circle(image, tuple(center), radius, (0, 0, 255), 2)

        
        # Draw anchor lines (anchor → eye center)
        cv2.line(image, anchor_points["left"], eye_centers["left"], (0, 255, 0), 2)   # Green
        cv2.line(image, anchor_points["right"], eye_centers["right"], (255, 0, 0), 2)  # Blue

        # Draw iris tracking lines (iris → eye center)
        cv2.line(image, iris_centers["left"], eye_centers["left"], (255, 0, 255), 2)   # Magenta
        cv2.line(image, iris_centers["right"], eye_centers["right"], (0, 255, 255), 2)  # Yellow

        # Compute angles for both eyes
        vec_l1 = np.array(eye_centers["left"]) - np.array(anchor_points["left"])
        vec_l2 = np.array(eye_centers["left"]) - np.array(iris_centers["left"])
        left_angle = self.vector_angle(vec_l1, vec_l2)

        vec_r1 = np.array(eye_centers["right"]) - np.array(anchor_points["right"])
        vec_r2 = np.array(eye_centers["right"]) - np.array(iris_centers["right"])
        right_angle = self.vector_angle(vec_r1, vec_r2)
        # Grade based on angles
        left_grade = self.grade_overaction(left_angle)
        right_grade = self.grade_overaction(right_angle)

        # Display grades on image
        cv2.putText(image, f"Left Overaction Grade: {left_grade}", (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(image, f"Right Overaction Grade: {right_grade}", (30, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)


        # Display the angles on the image
        cv2.putText(image, f"Left angle: {left_angle:.2f} deg", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(image, f"Right angle: {right_angle:.2f} deg", (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        '''# Optional: flagging overaction (example threshold, can be tuned)
        if left_angle - right_angle > 5:
            cv2.putText(image, "Possible Levo Overaction", (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)'''

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

if __name__ == "__main__":
    detector = EyeIrisDetector()
    result_img =detector.run_on_image(r"C:\Users\Karri\Documents\WIN_20250515_17_23_00_Pro.jpg")  # Replace with your left gaze image
    # Save the result if needed
    if result_img is not None:
        cv2.imwrite("overaction_grad_levo.jpg", result_img)

