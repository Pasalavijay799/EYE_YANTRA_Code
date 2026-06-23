'''
import os
import cv2
import numpy as np
from eye_detection import check_eye_status  # Assuming eye analysis is needed

# Function to analyze 9 gaze images and generate results
def process_nine_gaze_images(name, gaze_folder, output_folder):
    captured_images = [f"gaze_{i}.jpg" for i in range(1, 10)]
    
    person_input_path = os.path.join(gaze_folder, name)
    person_output_path = os.path.join(output_folder, f"{name}_Areal")
    
    if not os.path.exists(person_output_path):
        os.makedirs(person_output_path)

    areal_ratios = {}

    for image_name in captured_images:
        image_path = os.path.join(person_input_path, image_name)

        if not os.path.exists(image_path):
            return f"⚠️ Missing image: {image_name}", 400

        # Perform eye status check
        eye_status = check_eye_status(image_path)
        if "closed" in eye_status.lower() or "no face detected" in eye_status.lower():
            return f"⚠️ Issue detected in {image_name}: {eye_status}", 400

        # Dummy processing: Simulating areal ratio calculation
        areal_ratio = np.random.uniform(0.8, 1.2)  # Replace with actual computation
        areal_ratios[image_name] = areal_ratio

        # Simulated processing step (e.g., adding markers)
        img = cv2.imread(image_path)
        processed_img_path = os.path.join(person_output_path, image_name)
        cv2.imwrite(processed_img_path, img)  # Replace with actual processing

    # Save areal ratios in a text file
    text_file_path = os.path.join(person_output_path, "areal_ratios.txt")
    with open(text_file_path, "w") as f:
        for gaze, ratio in areal_ratios.items():
            f.write(f"{gaze}: {ratio:.3f}\n")

    return f"✅ 9 Gaze Analysis Completed. Results saved in {person_output_path}", 200

'''

import os
import cv2
import numpy as np
import math
import mediapipe as mp
from NineGazeDextro import EyeAnalyzer
from crop_eyes_from_image import crop_eyes_from_image
# Initialize MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

# Eye and Iris Landmark Indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Function to compute Euclidean Distance
def euclidean_distance(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)

# Function to compute Eye Aspect Ratio (EAR)
def blink_ratio(landmarks, img_width, img_height):
    def to_pixel_coords(lm):
        return int(lm.x * img_width), int(lm.y * img_height)

    # Convert landmark positions
    rh_right, rh_left = to_pixel_coords(landmarks[33]), to_pixel_coords(landmarks[133])
    rv_top, rv_bottom = to_pixel_coords(landmarks[159]), to_pixel_coords(landmarks[145])
    lh_right, lh_left = to_pixel_coords(landmarks[362]), to_pixel_coords(landmarks[263])
    lv_top, lv_bottom = to_pixel_coords(landmarks[386]), to_pixel_coords(landmarks[374])

    # Compute distances
    rh_dist, rv_dist = euclidean_distance(rh_right, rh_left), euclidean_distance(rv_top, rv_bottom)
    lh_dist, lv_dist = euclidean_distance(lh_right, lh_left), euclidean_distance(lv_top, lv_bottom)

    # Prevent division by zero
    if rv_dist == 0 or lv_dist == 0:
        return 0, 0

    return rh_dist / rv_dist, lh_dist / lv_dist  # Right & Left EAR

# Function to create eye masks
def create_eye_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    eye_pts = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [eye_pts], 255)
    return mask

# Function to create iris masks
def create_iris_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    iris_pts = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_pts)
    center, radius = (int(x), int(y)), int(radius)
    cv2.circle(mask, center, radius, 255, -1)
    return mask

# Function to analyze 9 gaze images
'''
def process_nine_gaze_images(name, gaze_folder="9GazeTestImages", output_folder="9GazeResults"):
    person_input_path = os.path.join(gaze_folder, name)
    person_output_path = os.path.join(output_folder, f"{name}_Areal")

    if not os.path.exists(person_output_path):
        os.makedirs(person_output_path)

    areal_ratios = {}

    for i in range(1, 10):
        image_name = f"gaze_{i}.jpg"
        image_path = os.path.join(person_input_path, image_name)

        if not os.path.exists(image_path):
            return f"⚠️ Missing image: {image_name}", 400

        # Load Image
        frame = cv2.imread(image_path)
        if frame is None:
            return f"⚠️ Error loading {image_name}", 400

        img_height, img_width = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process Image using MediaPipe
        results = face_mesh.process(frame_rgb)
        if not results.multi_face_landmarks:
            return f"⚠️ No face detected in {image_name}", 400

        for face_landmarks in results.multi_face_landmarks:
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * img_width), int(lm.y * img_height)) for lm in face_landmarks.landmark]

            # Compute EAR
            re_ratio, le_ratio = blink_ratio(face_landmarks.landmark, img_width, img_height)

            # Create masks
            left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
            right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
            left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
            right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

            # Find intersections
            left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
            right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)

            # Compute areal ratios
            left_area = cv2.countNonZero(left_intersection)
            right_area = cv2.countNonZero(right_intersection)

            if left_area > 0 and right_area > 0 and le_ratio <= 5 and re_ratio <= 5:
                areal_ratio = right_area / left_area
                areal_ratios[image_name] = areal_ratio
                cv2.putText(frame, f"Ratio: {areal_ratio:.2f}", (20, 138), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 0, 0), 2)
            elif le_ratio > 5:
                return f"⚠️ Left Eye Closed in {image_name}", 400
            elif re_ratio > 5:
                return f"⚠️ Right Eye Closed in {image_name}", 400

            # Highlight intersections
            frame[left_intersection == 255] = (0, 255, 255)
            frame[right_intersection == 255] = (0, 255, 255)

            # Save processed image
            processed_img_path = os.path.join(person_output_path, image_name)
            cv2.imwrite(processed_img_path, frame)

    # Save areal ratios to file
    text_file_path = os.path.join(person_output_path, "areal_ratios.txt")
    with open(text_file_path, "w") as f:
        for gaze, ratio in areal_ratios.items():
            f.write(f"{gaze}: {ratio:.3f}\n")

    return f"✅ 9 Gaze Analysis Completed. Results saved in {person_output_path}", 200'''





def process_nine_gaze_images(name, gaze_folder="AVK_GOVIND", output_folder="9GazeResults"):
    person_input_path = os.path.join(gaze_folder, name)
    areal_output_path = os.path.join(output_folder, f"{name}_Areal")
    remaining_results_path = os.path.join("9gazeRemainingResults", name)

    if not os.path.exists(areal_output_path):
        os.makedirs(areal_output_path)
    if not os.path.exists(remaining_results_path):
        os.makedirs(remaining_results_path)

    analyzer = EyeAnalyzer()
    all_results = {}
    areal_ratios = {}

    for i in range(1, 10):
        image_name = f"gaze_{i}.jpg"
        image_path = os.path.join(person_input_path, image_name)

        if not os.path.exists(image_path):
            return f"⚠️ Missing image: {image_name}", 400

        frame = cv2.imread(image_path)
        if frame is None:
            return f"⚠️ Error loading {image_name}", 400

        img_height, img_width = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame with EyeAnalyzer
        if i in [3, 6, 9]:
            gaze_dir = "dextro"
        elif i in [1, 4, 7]:
            gaze_dir = "levo"
        else:
            gaze_dir = "center"

        result = analyzer.process_frame(frame, gaze_direction=gaze_dir)
        processed_frame = result["processed_frame"]

        # Save processed frame to 9GazeResults
        processed_img_path = os.path.join(areal_output_path, image_name)
        cv2.imwrite(processed_img_path, processed_frame)
        crop_eyes_from_image(processed_img_path)

        # Save frame to 9gazeRemainingResults
        renamed_frame = f"{gaze_dir}_gaze_{i}.jpg"
        remaining_img_path = os.path.join(remaining_results_path, renamed_frame)
        cv2.imwrite(remaining_img_path, processed_frame)

        # Save grades and distances
        all_results[image_name] = {
            "distances": result["distances"],
            "grades": result["grades"]
        }

        # --- Area-based logic ---
        results_mp = face_mesh.process(frame_rgb)
        if not results_mp.multi_face_landmarks:
            return f"⚠️ No face detected in {image_name}", 400

        for face_landmarks in results_mp.multi_face_landmarks:
            landmarks = [(int(lm.x * img_width), int(lm.y * img_height)) for lm in face_landmarks.landmark]
            re_ratio, le_ratio = blink_ratio(face_landmarks.landmark, img_width, img_height)

            left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
            right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
            left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
            right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

            left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
            right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)

            left_area = cv2.countNonZero(left_intersection)
            right_area = cv2.countNonZero(right_intersection)

            if left_area > 0 and right_area > 0 and le_ratio <= 5 and re_ratio <= 5:
                areal_ratio = right_area / left_area
                areal_ratios[image_name] = areal_ratio
            elif le_ratio > 5:
                return f"⚠️ Left Eye Closed in {image_name}", 400
            elif re_ratio > 5:
                return f"⚠️ Right Eye Closed in {image_name}", 400

    # Save Grades Summary
    summary_path = os.path.join(areal_output_path, f"{name}_grades_summary.txt")
    with open(summary_path, 'w') as f:
        for img_name, data in all_results.items():
            f.write(f"Image: {img_name}\nGrades:\n")
            for k, v in data["grades"].items():
                f.write(f"  {k}: {v}\n")
            f.write("Distances:\n")
            for k, v in data["distances"].items():
                f.write(f"  {k}: {v:.2f}\n")
            f.write("\n")

    # Save Areal Ratios
    areal_path = os.path.join(areal_output_path, "areal_ratios.txt")
    with open(areal_path, "w") as f:
        for gaze, ratio in areal_ratios.items():
            f.write(f"{gaze}: {ratio:.3f}\n")

    return f"✅ Integrated 9-Gaze processing completed for {name}", 200
