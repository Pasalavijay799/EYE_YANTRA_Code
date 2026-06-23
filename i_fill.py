'''
import cv2 as cv
import mediapipe as mp
import numpy as np

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
EYE_BORDER = list(range(36, 48))  # Adjust indices for different eye regions if needed

# Initialize webcam
cap = cv.VideoCapture(0)  # Use 0 for default webcam
if not cap.isOpened():
    print("Error: Unable to access the webcam.")
    exit()

# Initialize Mediapipe FaceMesh
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read frame.")
            break

        # Convert frame to RGB for Mediapipe processing
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        img_h, img_w = frame.shape[:2]
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            mesh_points = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int)
                                    for p in results.multi_face_landmarks[0].landmark])

            # Highlight left and right irises with green dots
            for idx in LEFT_IRIS:
                cv.circle(frame, tuple(mesh_points[idx]), 2, (0, 255, 0), -1)  # Green dots for left iris
            for idx in RIGHT_IRIS:
                cv.circle(frame, tuple(mesh_points[idx]), 2, (0, 255, 0), -1)  # Green dots for right iris

            # Draw filled circles for pupils
            (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_IRIS])
            (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_IRIS])

            center_left = np.array([l_cx, l_cy], dtype=np.int32)
            center_right = np.array([r_cx, r_cy], dtype=np.int32)

            cv.circle(frame, center_left, int(l_radius), (255, 0, 0), -1)  # Fill left pupil (Blue)
            cv.circle(frame, center_right, int(r_radius), (255, 0, 0), -1)  # Fill right pupil (Blue)

            # Optionally: Add a yellow border around the eyes
            for idx in EYE_BORDER:
                if idx < len(mesh_points):  # Ensure index is within bounds
                    cv.circle(frame, tuple(mesh_points[idx]), 2, (0, 255, 255), -1)  # Yellow border

        # Display the frame
        cv.imshow('Pupil and Eyes Detection', frame)

        # Quit on pressing 'q'
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv.destroyAllWindows()





import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

# Drawing specifications
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Function to draw polygons and fill them
def draw_eye(image, landmarks, points, color):
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.polylines(image, [eye_points], isClosed=True, color=color, thickness=2)
    cv2.fillPoly(image, [eye_points], color)

# Capture from webcam or input image
cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with image path

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            # Draw left and right eye outlines and fill them
            draw_eye(frame, landmarks, LEFT_EYE, (255, 0, 0))  # Left eye in blue
            draw_eye(frame, landmarks, RIGHT_EYE, (255, 0, 0))  # Right eye in green

            # Draw left and right irises and fill them
            draw_eye(frame, landmarks, LEFT_IRIS, (255, 255, 0))  # Left iris in red
            draw_eye(frame, landmarks, RIGHT_IRIS, (255, 255, 0))  # Right iris in yellow

    cv2.imshow('Eye and Iris Drawing', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''



'''
import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

# Landmarks for eyes and irises
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Capture from webcam or input image
cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with image path

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            # Draw left eye and right eye outlines
            cv2.polylines(frame, [np.array([landmarks[p] for p in LEFT_EYE], dtype=np.int32)], isClosed=True, color=(255, 0, 0), thickness=2)
            cv2.polylines(frame, [np.array([landmarks[p] for p in RIGHT_EYE], dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

            # Compute and draw enclosing circles for the irises
            # Left iris
            (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(np.array([landmarks[p] for p in LEFT_IRIS]))
            center_left = (int(l_cx), int(l_cy))
            cv2.circle(frame, center_left, int(l_radius), (0, 0, 255), 2)  # Left iris in red

            # Right iris
            (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(np.array([landmarks[p] for p in RIGHT_IRIS]))
            center_right = (int(r_cx), int(r_cy))
            cv2.circle(frame, center_right, int(r_radius), (255, 255, 0), 2)  # Right iris in yellow

    # Display the frame
    cv2.imshow('Eye and Iris Drawing', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''
'''
%best code
import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

# Drawing specifications
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Function to draw polygons and fill them
def draw_eye(image, landmarks, points, color):
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.polylines(image, [eye_points], isClosed=True, color=color, thickness=2)
    cv2.fillPoly(image, [eye_points], color)

# Function to draw a circle around the iris
def draw_iris_circle(image, landmarks, points, color):
    iris_points = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_points)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(image, center, radius, color, thickness=2)
    cv2.circle(image, center, radius, color, thickness=-1)  # Fill the circle

# Capture from webcam or input image
cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with image path

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            # Draw left and right eye outlines and fill them
            draw_eye(frame, landmarks, LEFT_EYE, (255, 0, 0))  # Left eye in blue
            draw_eye(frame, landmarks, RIGHT_EYE, (255, 0, 0))  # Right eye in green

            # Draw left and right irises using a minimal enclosing circle
            draw_iris_circle(frame, landmarks, LEFT_IRIS, (255, 255, 0))  # Left iris in yellow
            draw_iris_circle(frame, landmarks, RIGHT_IRIS, (255, 255, 0))  # Right iris in yellow

    cv2.imshow('Eye and Iris Drawing', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''

'''
#best code


import cv2
import mediapipe as mp
import numpy as np

# Initialize Mediapipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

# Drawing specifications
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]



# Function to draw polygons and fill them
def draw_eye(image, landmarks, points, color):
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.polylines(image, [eye_points], isClosed=True, color=color, thickness=2)
    #cv2.fillPoly(image, [eye_points], color)



# Function to create a filled mask for the eye
def create_eye_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [eye_points], 255)
    return mask


# Function to draw a circle around the iris
def draw_iris_circle(image, landmarks, points, color):
    iris_points = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_points)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(image, center, radius, color, thickness=2)
    #cv2.circle(image, center, radius, color, thickness=-1)  # Fill the circle



# Function to add labels to the eyes
def add_eye_labels(image, landmarks, eye_points, label, color):
    # Get the centroid of the eye landmarks
    points = np.array([landmarks[p] for p in eye_points], dtype=np.int32)
    M = cv2.moments(points)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        position = (cx - 30, cy - 20)  # Adjust position slightly above the eye
        cv2.putText(image, label, position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)



# Function to create a filled mask for the iris
def create_iris_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    iris_points = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_points)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(mask, center, radius, 255, thickness=-1)
    return mask

# Capture from webcam or input image
cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with image path

while cap.isOpened():
    ret, frame = cap.read()
    #frame=cv2.flip(frame,1)
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = face_mesh.process(frame_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            # Create eye masks
            left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
            right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)

            # Create iris masks
            left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
            right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)

            # Find intersection of iris and eye masks
            left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
            right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)

            # Draw the intersection on the frame
            frame[left_intersection == 255] = (0, 255, 255)  # Intersection in yellow
            frame[right_intersection == 255] = (0, 255, 255)  # Intersection in yellow

            # Optionally draw eyes and irises
            ##draw_eye(frame, landmarks, LEFT_EYE, (255, 0, 0))  # Left eye in blue
            ##draw_eye(frame, landmarks, RIGHT_EYE, (255, 0, 0))  # Right eye in green
            ##draw_iris_circle(frame, landmarks, LEFT_IRIS, (255, 255, 0))  # Left iris in yellow
            ##draw_iris_circle(frame, landmarks, RIGHT_IRIS, (255, 255, 0))  # Right iris in yellow
            # Add labels for left and right eyes
            add_eye_labels(frame, landmarks, LEFT_EYE, "Left Eye", (0, 255, 0))  # Green label for left eye
            add_eye_labels(frame, landmarks, RIGHT_EYE, "Right Eye", (0, 0, 255))  # Red label for right eye

    cv2.imshow('Eye and Iris Drawing with Intersection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''





import cv2
import mediapipe as mp
import numpy as np
import math

# Mediapipe Face Mesh Initialization
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# Eye and Iris Landmark Indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Function to compute Euclidean Distance
def euclidean_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)




# Function to draw polygons and fill them
def draw_eye(image, landmarks, points, color):
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.polylines(image, [eye_points], isClosed=True, color=color, thickness=2)
    #cv2.fillPoly(image, [eye_points], color)



# Function to create a filled mask for the eye
def create_eye_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [eye_points], 255)
    return mask

# Function to create a filled mask for the iris
def create_iris_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    iris_points = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_points)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(mask, center, radius, 255, thickness=-1)
    return mask

# Function to calculate EAR (Eye Aspect Ratio)
def blink_ratio(frame, landmarks, img_width, img_height):
    def to_pixel_coords(landmark):
        return int(landmark.x * img_width), int(landmark.y * img_height)

    # Right Eye Landmarks
    rh_right = to_pixel_coords(landmarks[33])
    rh_left = to_pixel_coords(landmarks[133])
    rv_top =  to_pixel_coords(landmarks[159])
    rv_bottom = to_pixel_coords(landmarks[145])
    # Left Eye Landmarks
    lh_right = to_pixel_coords(landmarks[362])
    lh_left = to_pixel_coords(landmarks[263])
    lv_top =to_pixel_coords(landmarks[386])
    lv_bottom = to_pixel_coords(landmarks[374])


    # Right Eye Ratios
    rh_distance = euclidean_distance(rh_right, rh_left)
    rv_distance = euclidean_distance(rv_top, rv_bottom)

    # Left Eye Ratios
    lh_distance = euclidean_distance(lh_right, lh_left)
    lv_distance = euclidean_distance(lv_top, lv_bottom)

    # Prevent division by zero
    if rv_distance == 0 or lv_distance == 0:
        return 0, 0

    # Eye Aspect Ratios
    re_ratio = rh_distance / rv_distance
    le_ratio = lh_distance / lv_distance

    return re_ratio, le_ratio

# Function to draw eyes
def draw_eye(image, landmarks, points, color):
    eye_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.polylines(image, [eye_points], isClosed=True, color=color, thickness=2)

# Function to draw iris
def draw_iris_circle(image, landmarks, points, color):
    iris_points = np.array([landmarks[p] for p in points], dtype=np.float32)
    (x, y), radius = cv2.minEnclosingCircle(iris_points)
    center = (int(x), int(y))
    radius = int(radius)
    cv2.circle(image, center, radius, color, thickness=2)

# Function to add eye labels
def add_eye_labels(image, landmarks, eye_points, label, color):
    points = np.array([landmarks[p] for p in eye_points], dtype=np.int32)
    M = cv2.moments(points)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        position = (cx - 30, cy - 20)  # Adjust position slightly above the eye
        cv2.putText(image, label, position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

# Function to create a filled mask
def create_mask(image_shape, landmarks, points):
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    key_points = np.array([landmarks[p] for p in points], dtype=np.int32)
    cv2.fillPoly(mask, [key_points], 255)
    return mask

# Webcam capture
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_height, img_width = frame.shape[:2]

    # Process the frame
    results = face_mesh.process(frame_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Convert landmarks to pixel coordinates
            landmarks = [(int(lm.x * img_width), int(lm.y * img_height)) for lm in face_landmarks.landmark]

            # EAR Calculation
            re_ratio, le_ratio = blink_ratio(frame, face_landmarks.landmark, img_width, img_height)
            if not re_ratio>=6 and not le_ratio>=6:
            	# Create eye masks
            	left_eye_mask = create_eye_mask(frame.shape, landmarks, LEFT_EYE)
            	right_eye_mask = create_eye_mask(frame.shape, landmarks, RIGHT_EYE)
            	# Create iris masks
            	left_iris_mask = create_iris_mask(frame.shape, landmarks, LEFT_IRIS)
            	right_iris_mask = create_iris_mask(frame.shape, landmarks, RIGHT_IRIS)
            	# Find intersection of iris and eye masks
            	left_intersection = cv2.bitwise_and(left_eye_mask, left_iris_mask)
            	right_intersection = cv2.bitwise_and(right_eye_mask, right_iris_mask)
            	# Draw the intersection on the frame
            	frame[left_intersection == 255] = (0, 255, 255)  # Intersection in yellow
            	frame[right_intersection == 255] = (0, 255, 255)  # Intersection in yellow
            	# Calculate intersection areas in pixels
            	left_area = cv2.countNonZero(left_intersection)
            	right_area = cv2.countNonZero(right_intersection)
            	# Display areas on the frame
            	cv2.putText(frame, f"Left Intersection Area: {left_area}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            	cv2.putText(frame, f"Right Intersection Area: {right_area}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            elif re_ratio>=6:
            	cv2.putText(frame, "Right closed", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            	
            elif le_ratio>=6:
            	cv2.putText(frame, "Left  closed", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            	
            # Display EAR Ratios
            cv2.putText(frame, f"EAR Left Eye: {le_ratio:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"EAR Right Eye: {re_ratio:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Draw Eyes
            ##draw_eye(frame, landmarks, LEFT_EYE, (255, 0, 0))  # Left eye in blue
            ##draw_eye(frame, landmarks, RIGHT_EYE, (0, 255, 0))  # Right eye in green

            # Draw Iris Circles
            ##draw_iris_circle(frame, landmarks, LEFT_IRIS, (255, 255, 0))  # Left iris in yellow
            ##draw_iris_circle(frame, landmarks, RIGHT_IRIS, (0, 255, 255))  # Right iris in cyan

            # Add Labels
            add_eye_labels(frame, landmarks, LEFT_EYE, "Left Eye", (255, 255, 255))
            add_eye_labels(frame, landmarks, RIGHT_EYE, "Right Eye", (255, 255, 255))
            
            


    cv2.imshow("Eye Blink Detector with EAR", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

