import os
import cv2
from flask import render_template, session, redirect, url_for
from datetime import datetime
from eye_detection import check_eye_status  # Import eye detection function
from crop_eyes_from_image import crop_eyes_from_image
import mediapipe as mp
import numpy as np
import math


# Define iris landmark indices
LEFT_IRIS = [469, 470, 471, 472]  # Mediapipe iris landmarks for the left eye
RIGHT_IRIS = [474, 475, 476, 477]  # Mediapipe iris landmarks for the right eye
# Define the eye landmarks
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]



# Define folders (Ensure these paths are correct in your project)
PRELIMINARY_FOLDER = "preliminary"
PreliminaryResults_Folder = "Preliminary_Results"

def show_results(userName=None, personDetails=None, connected_device=None):
    try:
        # Get the latest image based on modification time
        images = sorted(
            [f for f in os.listdir(PRELIMINARY_FOLDER) if f.endswith((".jpg", ".png"))],
            key=lambda f: os.path.getmtime(os.path.join(PRELIMINARY_FOLDER, f)),
            reverse=True
        )  

        if not images:
            session["error_message"] = "❌ No images found. Please capture an image first."
            return redirect(url_for("preliminary_test"))

        latest_image = images[0]
        image_path = os.path.join(PRELIMINARY_FOLDER, latest_image)

        # Check eye status
        # eye_status = check_eye_status(image_path)
        # print(f"🔍 Eye status: {eye_status}")
        # if "⚠️" in eye_status:
        #     session["error_message"] = eye_status  
        #     return redirect(url_for("preliminary_test"))

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            session["error_message"] = "❌ Could not load image. Please try again."
            return redirect(url_for("preliminary_test"))

        # Convert to grayscale
        '''
        processed_filename = latest_image  
        processed_path = os.path.join(PreliminaryResults_Folder, processed_filename)

        # Save processed image
        
        cv2.imwrite(processed_path, processed_frame)

        # Create text file with details
        text_filename = processed_filename.replace(".jpg", ".txt").replace(".png", ".txt")
        text_path = os.path.join(PreliminaryResults_Folder, text_filename)

        with open(text_path, "w") as file:
            file.write(f"Processed Image: {processed_filename}\n")
            file.write(f"Original Image: {latest_image}\n")
            file.write("Processing: Grayscale conversion\n")'''
        

        processed_filename = latest_image  
        print("processed_filename:",processed_filename)
        processed_path = os.path.join(PreliminaryResults_Folder, processed_filename)

        image, text_content,text_filename=analyze_eyes(image,processed_path,processed_filename)
        # Debugging URL generation
        print("🔍 Debugging URLs for processed files:")
        print(url_for('download_image', test_type='preliminary', filename=processed_filename))
        print(url_for('download_text', test_type='preliminary', filename=text_filename))

        return render_template(
            "Preliminary_Results.html",
            status="success",
            message="✅ Eyes detected as open, proceeding to results.",
            processed_image=processed_filename,
            text_file=text_filename,
            test_type="preliminary",
            userName=userName,
            personDetails=personDetails,
            connected=connected_device
        )

    except Exception as e:
        session["error_message"] = f"❌ Error: {str(e)}"
        return redirect(url_for("preliminary_test"))





def calculate_rectangle_points(x, y, w, h):
    """
    Calculate the center and midpoints of the sides of a rectangle.
    
    Parameters:
    x (int): x-coordinate of the top-left corner of the rectangle
    y (int): y-coordinate of the top-left corner of the rectangle
    w (int): Width of the rectangle
    h (int): Height of the rectangle

    Returns:
    dict: A dictionary containing the center and the midpoints of the four sides
    """
    # Calculate the center of the rectangle
    center_x = x + w / 2
    center_y = y + h / 2

    # Calculate midpoints of the four sides
    points = {
        "center": (center_x, center_y),
        "top_midpoint": (x + w / 2, y),
        "bottom_midpoint": (x + w / 2, y + h),
        "left_midpoint": (x, y + h / 2),
        "right_midpoint": (x + w, y + h / 2)
    }

    return points




'''
def calculate_angle(line1, line2):
    """
    Calculate the angle (in degrees) between two lines defined by their endpoints.
    
    Parameters:
        line1: tuple of tuples ((x1, y1), (x2, y2)) - Endpoints of the first line.
        line2: tuple of tuples ((x3, y3), (x4, y4)) - Endpoints of the second line.
    
    Returns:
        angle_degrees: float - The angle between the two lines in degrees.
    """
    # Extract endpoints
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2

    # Calculate direction vectors
    v1 = np.array([x2 - x1, y2 - y1])
    v2 = np.array([x4 - x3, y4 - y3])

    # Calculate dot product and magnitudes
    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)

    # Handle edge case: zero-length vectors
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        raise ValueError("One of the lines has zero length.")

    # Calculate cosine of the angle
    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)

    # Clamp cosine to avoid numerical errors
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    # Calculate the angle in radians and convert to degrees
    angle_radians = np.arccos(cos_theta)
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees
'''


def calculate_angle(line1, line2):
    """
    Calculate the angle (in degrees) between two lines defined by their endpoints.
    
    Parameters:
        line1: tuple of tuples ((x1, y1), (x2, y2)) - Endpoints of the first line (fixed line).
        line2: tuple of tuples ((x3, y3), (x4, y4)) - Endpoints of the second line.
    
    Returns:
        angle_degrees: float - The angle between the two lines in degrees.
                          Positive if the second line is on the right, negative if on the left.
    """
    # Extract endpoints
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2

    # Calculate direction vectors
    v1 = np.array([x2 - x1, y2 - y1])  # Vector for the fixed line
    v2 = np.array([x4 - x3, y4 - y3])  # Vector for the second line

    # Calculate dot product and magnitudes
    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)

    # Handle edge case: zero-length vectors
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        raise ValueError("One of the lines has zero length.")

    # Calculate cosine of the angle
    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)

    # Clamp cosine to avoid numerical errors
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    # Calculate the angle in radians
    angle_radians = np.arccos(cos_theta)

    # Determine the sign of the angle using the cross product
    '''cross_product = np.cross(v1, v2)  # Scalar in 2D
    if cross_product < 0:
        angle_radians = -angle_radians'''

    # Convert angle to degrees
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees
    
    
    
    
    







def calculate_centroid(points):
    """Calculate the centroid of a set of points."""
    centroid_x = np.mean(points[:, 0])
    centroid_y = np.mean(points[:, 1])
    return (int(centroid_x), int(centroid_y))

def calculate_distance(point1, point2):
    """Calculate the Euclidean distance between two points."""
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)


def analyze_eyes(image,processed_path,processed_filename):
    """Process image to analyze eyes, detect canthus positions, and calculate distances."""
    text_content = f"Preliminary test  Analysis Report\n\n"
    text_content += f"Input Image Path: {processed_filename}\n \n"
    mp_face_mesh = mp.solutions.face_mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                img_h, img_w, _ = image.shape
                
                # Extract landmark points
                right_lateral_canthus = face_landmarks.landmark[33]
                right_medial_canthus = face_landmarks.landmark[133]
                left_lateral_canthus = face_landmarks.landmark[263]
                left_medial_canthus = face_landmarks.landmark[362]
                rv_top = face_landmarks.landmark[159]
                rv_bottom = face_landmarks.landmark[145]
                lv_top = face_landmarks.landmark[386]
                lv_bottom = face_landmarks.landmark[374]

                # Convert to pixel coordinates
                right_lateral_canthus_coords = (int(right_lateral_canthus.x * img_w), int(right_lateral_canthus.y * img_h))
                right_medial_canthus_coords = (int(right_medial_canthus.x * img_w), int(right_medial_canthus.y * img_h))
                left_lateral_canthus_coords = (int(left_lateral_canthus.x * img_w), int(left_lateral_canthus.y * img_h))
                left_medial_canthus_coords = (int(left_medial_canthus.x * img_w), int(left_medial_canthus.y * img_h))
                lv_top_coords = (int(lv_top.x * img_w), int(lv_top.y * img_h))
                lv_bottom_coords = (int(lv_bottom.x * img_w), int(lv_bottom.y * img_h))
                rv_top_coords = (int(rv_top.x * img_w), int(rv_top.y * img_h))
                rv_bottom_coords = (int(rv_bottom.x * img_w), int(rv_bottom.y * img_h))

                left_eye_landmarks = [face_landmarks.landmark[i] for i in LEFT_EYE]
                right_eye_landmarks = [face_landmarks.landmark[i] for i in RIGHT_EYE]
                # Extract iris landmarks
                left_iris_landmarks = [face_landmarks.landmark[i] for i in LEFT_IRIS]
                right_iris_landmarks = [face_landmarks.landmark[i] for i in RIGHT_IRIS]
                # Convert iris landmarks to pixel coordinates and calculate the centroids
                left_eye_coords = [(int(landmark.x * img_w), int(landmark.y * img_h)) for landmark in left_eye_landmarks]
                right_eye_coords = [(int(landmark.x * img_w), int(landmark.y * img_h)) for landmark in right_eye_landmarks]
                left_iris_coords = [(int(landmark.x * img_w), int(landmark.y * img_h)) for landmark in left_iris_landmarks]
                right_iris_coords = [(int(landmark.x * img_w), int(landmark.y * img_h)) for landmark in right_iris_landmarks]

                # Calculate pupil centers
                right_pupil_center = calculate_centroid(np.array(left_iris_coords, np.int32))
                left_pupil_center = calculate_centroid(np.array(right_iris_coords, np.int32))

                # Draw circles for key points
                cv2.circle(image, right_pupil_center, 2, (0, 255, 0), -1)
                cv2.circle(image, left_pupil_center, 2, (0, 255, 0), -1)
                
                frame=image
                cv2.polylines(frame, [np.array(left_eye_coords, np.int32)], isClosed=True, color=(255, 0, 0), thickness=1)  # Blue for left eye
                cv2.polylines(frame, [np.array(right_eye_coords, np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)  # Green for right eye
                left_eye_rect = cv2.boundingRect(np.array(left_eye_coords, np.int32))
                right_eye_rect = cv2.boundingRect(np.array(right_eye_coords, np.int32))
                cv2.rectangle(frame, (left_eye_rect[0], left_eye_rect[1]), (left_eye_rect[0] + left_eye_rect[2], left_eye_rect[1] + left_eye_rect[3]), (255, 0, 0), 2)  # Blue rectangle for left eye
                cv2.rectangle(frame, (right_eye_rect[0], right_eye_rect[1]), (right_eye_rect[0] + right_eye_rect[2], right_eye_rect[1] + right_eye_rect[3]), (0, 255, 0), 2)  # Green rectangle for right eye
                
                
                
                left_eye_rect = (left_eye_rect[0],left_eye_rect[1], left_eye_rect[2], left_eye_rect[3])  # Example values for left eye (x, y, w, h)
                right_eye_rect = (right_eye_rect[0], right_eye_rect[1], right_eye_rect[2], right_eye_rect[3])  # Example values for right eye (x, y, w, h)
                # Calculate points for each rectangle
                left_eye_points = calculate_rectangle_points(*left_eye_rect)
                right_eye_points = calculate_rectangle_points(*right_eye_rect)
                # Display results
                print("Left Eye:")
                print("  Center:", (left_eye_points["center"]))
                #cv2.putText(image, "LC", (int(left_eye_points["center"][0]), int(left_eye_points["center"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 255), 1)
                print("  Top Midpoint:", left_eye_points["top_midpoint"])
                cv2.putText(image, "LT", (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 1)  # Left Top
                print("  Bottom Midpoint:", left_eye_points["bottom_midpoint"])
                #cv2.putText(image, "LB", (int(left_eye_points["bottom_midpoint"][0]), int(left_eye_points["bottom_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 1)  # Left Bottom
                print("  Left Midpoint:", left_eye_points["left_midpoint"])
                #cv2.putText(image, "LL", (int(left_eye_points["left_midpoint"][0]), int(left_eye_points["left_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 1)  # Left Left
                print("  Right Midpoint:", left_eye_points["right_midpoint"])
                cv2.putText(image, "LR", (int(left_eye_points["right_midpoint"][0]), int(left_eye_points["right_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 1)  # Left Right
                print("\nRight Eye:")
                print("  Center:", right_eye_points["center"])
                #cv2.putText(image, "RC", (int(right_eye_points["center"][0]), int(right_eye_points["center"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 255), 1)  # Right Center
                print("  Top Midpoint:", right_eye_points["top_midpoint"])
                cv2.putText(image, "RT", (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 1)  # Right Top
                print("  Bottom Midpoint:", right_eye_points["bottom_midpoint"])
                #cv2.putText(image, "RB", (int(right_eye_points["bottom_midpoint"][0]), int(right_eye_points["bottom_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 1)  # Right Bottom
                print("  Left Midpoint:", right_eye_points["left_midpoint"])
                #cv2.putText(image, "RL", (int(right_eye_points["left_midpoint"][0]), int(right_eye_points["left_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 1)  # Right Left
                print("  Right Midpoint:", right_eye_points["right_midpoint"])
                cv2.putText(image, "RR", (int(right_eye_points["right_midpoint"][0]), int(right_eye_points["right_midpoint"][1])),cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 1)  # Right Right
                
                
                # Draw the points
                for label, point in left_eye_points.items():
                    cv2.circle(image, (int(point[0]), int(point[1])), 1, (0, 255, 255), -1)  # Yellow points for left eye
                for label, point in right_eye_points.items():
                    cv2.circle(image, (int(point[0]), int(point[1])), 1, (255, 255, 0), -1)  # Cyan points for right eye  
                

                # Draw lines from canthus points to pupil centers
                cv2.line(image, right_lateral_canthus_coords, right_pupil_center, (0, 255, 255), 1)
                cv2.line(image, right_medial_canthus_coords, right_pupil_center, (255, 0, 255), 1)
                cv2.line(image, left_lateral_canthus_coords, left_pupil_center, (0, 255, 0), 1)
                cv2.line(image, left_medial_canthus_coords,left_pupil_center , (255, 0, 0), 1)
                cv2.line(image, lv_bottom_coords, left_pupil_center, (255, 255, 0), 1)
                cv2.line(image, lv_top_coords, left_pupil_center, (255, 255, 0), 1)
                cv2.line(image, rv_bottom_coords, right_pupil_center, (255, 255, 0), 1)
                cv2.line(image, rv_top_coords, right_pupil_center, (255, 255, 0), 1)      





                # Calculate distances
                dist_right_lateral = calculate_distance(right_lateral_canthus_coords, right_pupil_center)
                dist_right_medial = calculate_distance(right_medial_canthus_coords, right_pupil_center)
                dist_left_lateral = calculate_distance(left_lateral_canthus_coords, left_pupil_center)
                dist_left_medial = calculate_distance(left_medial_canthus_coords, left_pupil_center)
                dist_lv_top = calculate_distance(lv_top_coords, left_pupil_center)
                dist_lv_bottom = calculate_distance(lv_bottom_coords, left_pupil_center)
                dist_rv_top = calculate_distance(rv_top_coords, right_pupil_center)
                dist_rv_bottom = calculate_distance(rv_bottom_coords, right_pupil_center)
                dist_lv_top_coords = calculate_distance(lv_top_coords, left_pupil_center)
                dist_lv_bottom_coords = calculate_distance(lv_bottom_coords, left_pupil_center)
                dist_rv_top_coords = calculate_distance(rv_top_coords, right_pupil_center)
                dist_rv_bottom_coords = calculate_distance(rv_bottom_coords, right_pupil_center)

                # Print all calculated distances with clear labels
                print("\nCalculated Distances:")
                print(f"Distance from Right Lateral Canthus to Right Pupil Center: {dist_right_lateral:.2f}")
                print(f"Distance from Right Medial Canthus to Right Pupil Center: {dist_right_medial:.2f}")
                print(f"Distance from Left Lateral Canthus to Left Pupil Center: {dist_left_lateral:.2f}")
                print(f"Distance from Left Medial Canthus to Left Pupil Center: {dist_left_medial:.2f}")
                print(f"Distance from Left Vertical Top to Left Pupil Center: {dist_lv_top_coords:.2f}")
                print(f"Distance from Left Vertical Bottom to Left Pupil Center: {dist_lv_bottom_coords:.2f}")
                print(f"Distance from Right Vertical Top to Right Pupil Center: {dist_rv_top_coords:.2f}")
                print(f"Distance from Right Vertical Bottom to Right Pupil Center: {dist_rv_bottom_coords:.2f}")

                
                

                #print(dist_right_lateral,dist_right_medial,dist_left_lateral,dist_left_medial)
                S_V = max(dist_rv_top_coords / dist_rv_bottom_coords , dist_lv_top_coords / dist_lv_bottom_coords) / \
                    min(dist_rv_top_coords / dist_rv_bottom_coords , dist_lv_top_coords / dist_lv_bottom_coords)
                S = max(dist_right_medial / dist_right_lateral, dist_left_medial / dist_left_lateral) /min(dist_right_medial / dist_right_lateral, dist_left_medial / dist_left_lateral)
            

                if S>1.23:
                    if (dist_right_medial<dist_left_medial) :
                        if dist_right_medial<dist_right_lateral and dist_right_medial<dist_left_lateral :
                            print("Right Esotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            
                            right_estro_degree=calculate_angle(line1, line2)
                            if right_pupil_center[0]>right_eye_points["center"][0]:
                                right_estro_degree= -right_estro_degree
                            #cv2.putText(image, "right Esotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            text_content +=f"\nright Esotropia\n \n"
                            text_content +=f"\nright_estro_degree:{right_estro_degree:.2f}\n \n"
                            #cv2.putText(image, f"right_estro_degree:{right_estro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            print(right_estro_degree)
                        
                        
                        
                        
                        
                        elif dist_right_lateral<dist_left_lateral:
                            print("Right Exotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_extro_degree=calculate_angle(line1, line2)
                            if right_pupil_center[0]>right_eye_points["center"][0]:
                                right_estro_degree= -right_estro_degree
                            print("line1:", 
        (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),
        (int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
        

                            print(right_extro_degree)
                            print("line2:", 
        (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),
        (right_pupil_center))
                            #cv2.putText(image, "right Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            #cv2.putText(image, f"right_extro_degree:{right_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            text_content +=f"\nright Exotropia\n \n"
                            text_content +=f"\nright_extro_degree:{right_extro_degree:.2f}\n \n"
                        elif dist_right_lateral>dist_left_lateral:
                            print("left Exotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),left_pupil_center)
                            left_extro_degree=calculate_angle(line1, line2)
                            print(left_extro_degree)
                            #cv2.putText(image, "left Exotropia", (30, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            #cv2.putText(image, f"left extro degree wrt to LTP degree:{left_extro_degree}", (30, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            text_content +="left Exotropia\n"
                            text_content +=f"left extro degree wrt to LTP degree:{left_extro_degree}\n \n"
                    elif (dist_right_medial>dist_left_medial):
                        if dist_left_medial<dist_left_lateral and dist_left_medial<dist_right_lateral :
                            print("left Esotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),left_pupil_center)
                            
                            left_estro_degree=calculate_angle(line1, line2)
                            if left_pupil_center[0]<left_eye_points["top_midpoint"][0]:
                                left_estro_degree=-left_estro_degree
                            #cv2.putText(image, "left Esotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            print("line1:" ,(int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            print("line2:" ,(int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(left_pupil_center))
                            #cv2.putText(image, f"left_estro_degree:{left_estro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            print(left_estro_degree)
                            text_content +=f"\nleft Esotropia\n \n"
                            text_content +=f"\nleft_estro_degree:{left_estro_degree:.2f}\n \n"
                        elif dist_left_lateral<dist_right_lateral:
                            print("LEFT Exotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),left_pupil_center)
                            left_extro_degree=calculate_angle(line1, line2)
                            print(left_extro_degree)
                            #cv2.putText(image, "left Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            #cv2.putText(image, f"left_extro_degree:{left_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            text_content +="left Exotropia:"
                            text_content +=f"left_extro_degree:{left_extro_degree:.2f}"
                        elif dist_left_lateral>dist_right_lateral:
                            print("right Exotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_extro_degree=calculate_angle(line1, line2)
                            print(right_extro_degree)
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_extro_degree=calculate_angle(line1, line2)
                            print("line1:", 
        (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),
        (int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            print("line2:", 
        (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),
        (right_pupil_center))
                            #cv2.putText(image, "right Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            #cv2.putText(image, f"right_extro_degree:{right_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            text_content +="right Exotropia:"
                            text_content +=f"right_extro_degree:{right_extro_degree:.2f}"
                else:
                    print("No Horizontal Squint")
                    text_content +="\nNo Horizontal Squint\n"
                if S_V>1.5:
                    if (dist_rv_top_coords<dist_rv_bottom_coords and dist_rv_top_coords<dist_lv_top_coords and dist_rv_top_coords<dist_lv_bottom_coords ):
                        print("right hypertropia")
                        line1=( (int(right_eye_points["right_midpoint"][0]), int(right_eye_points["right_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                        line2=(  (int(right_eye_points["right_midpoint"][0]), int(right_eye_points["right_midpoint"][1])),right_pupil_center)
                        right_hyper_degree=calculate_angle(line1, line2)
                        #cv2.putText(image, "right_hyper_degree", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 255, 255), 2)
                        #cv2.putText(image, f"right_hyper_degree:{right_hyper_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        text_content +="right_hyper_degree:"
                        text_content +=f"right_hyper_degree:{right_hyper_degree:.2f}"
                        print(right_hyper_degree)
                        
                        
                        
                            
                    elif(dist_rv_top_coords>dist_rv_bottom_coords and dist_rv_bottom_coords<dist_lv_top_coords and dist_rv_bottom_coords<dist_lv_bottom_coords):
                        print("right hypotropia")
                        line1=( (int(right_eye_points["right_midpoint"][0]), int(right_eye_points["right_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                        line2=(  (int(right_eye_points["right_midpoint"][0]), int(right_eye_points["right_midpoint"][1])),right_pupil_center)
                        right_hypo_degree=calculate_angle(line1, line2)
                        if right_pupil_center[1]>right_eye_points["right_midpoint"][1]:
                            right_hypo_degree=-right_hypo_degree
                        #cv2.putText(image, "right_hypo_degree", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        #cv2.putText(image, f"right_hypo_degree:{right_hypo_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        print(right_hypo_degree)
                        text_content +=f"\nright_hypo_degree: {right_hypo_degree:.2f}\n"
                    elif (dist_lv_top_coords<dist_lv_bottom_coords and dist_lv_top_coords<dist_rv_top_coords and dist_lv_top_coords<dist_rv_bottom_coords ):
                        print("left hypertropia")
                        line1=( (int(left_eye_points["left_midpoint"][0]), int(left_eye_points["left_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                        line2=(  (int(left_eye_points["left_midpoint"][0]), int(left_eye_points["left_midpoint"][1])),left_pupil_center)
                        
                        left_hyper_degree=calculate_angle(line1, line2)
                        #cv2.putText(image, "left_hyper_degree", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        #cv2.putText(image, f"left_hyper_degree:{left_hyper_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        print(left_hyper_degree)
                        text_content +=f"left_hyper_degree:{left_hyper_degree:.2f}"
                    elif (dist_lv_top_coords>dist_lv_bottom_coords and dist_lv_bottom_coords<dist_rv_top_coords and dist_lv_bottom_coords<dist_rv_bottom_coords ):
                        print("left hypotropia")
                        line1=( (int(left_eye_points["right_midpoint"][0]), int(left_eye_points["right_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                        line2=(  (int(left_eye_points["right_midpoint"][0]), int(left_eye_points["right_midpoint"][1])),left_pupil_center)
                        
                        left_hypo_degree=calculate_angle(line1, line2)
                        if left_pupil_center[1]>left_eye_points["right_midpoint"][1]:
                            left_hypo_degree=-left_hypo_degree
                        #cv2.putText(image, "left_hypo_degree", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        #cv2.putText(image, f"left_hypo_degree:{left_hypo_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        print(left_hypo_degree)
                        text_content +=f"\nleft_hypo_degree: {left_hypo_degree:.2f}\n"
                        
                    
                    
                    
                    #dist_right_medial / dist_right_lateral > dist_left_medial / dist_left_lateral
                    '''
                    if (dist_right_medial<dist_left_medial) :
                        if dist_right_medial<dist_right_lateral and dist_right_medial<dist_left_lateral :
                            print("Right Esotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_estro_degree=calculate_angle(line1, line2)
                            cv2.putText(image, "right Esotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"right_estro_degree:{right_estro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            print(right_estro_degree)
                        elif dist_right_lateral<dist_left_lateral:
                            print("Right Exotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_extro_degree=calculate_angle(line1, line2)
                            print(right_extro_degree)
                            cv2.putText(image, "right Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"right_extro_degree:{right_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            
                            
                            
                        elif dist_right_lateral>dist_left_lateral:
                            print("left Exotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),left_pupil_center)
                            left_extro_degree=calculate_angle(line1, line2)
                            print(left_extro_degree)
                            cv2.putText(image, "left Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"left_extro_degree:{left_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            
                    elif (dist_right_medial>dist_left_medial):
                        if dist_left_medial<dist_left_lateral and dist_left_medial<dist_right_lateral :
                            print("left Esotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),right_pupil_center)
                            left_estro_degree=calculate_angle(line1, line2)
                            cv2.putText(image, "left Esotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"left_estro_degree:{left_estro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            print(left_estro_degree)
                        elif dist_left_lateral<dist_right_lateral:
                            print("LEFT Exotropia")
                            line1=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),(int(left_eye_points["center"][0]), int(left_eye_points["center"][1])))
                            line2=( (int(left_eye_points["top_midpoint"][0]), int(left_eye_points["top_midpoint"][1])),left_pupil_center)
                            left_extro_degree=calculate_angle(line1, line2)
                            print(left_extro_degree)
                            cv2.putText(image, "left Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"left_extro_degree:{left_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        elif dist_left_lateral>dist_right_lateral:
                            print("right Exotropia")
                            line1=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),(int(right_eye_points["center"][0]), int(right_eye_points["center"][1])))
                            line2=( (int(right_eye_points["top_midpoint"][0]), int(right_eye_points["top_midpoint"][1])),right_pupil_center)
                            right_extro_degree=calculate_angle(line1, line2)
                            print(right_extro_degree)
                            cv2.putText(image, "right Exotropia", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            cv2.putText(image, f"right_extro_degree:{right_extro_degree}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)'''
                else:
                    print("No Vertical squint")
                    text_content +="\nNo Vertical Squint\n"
                
                
                # Display distances and S value on the image
                #cv2.putText(image, f"HER: {round(S, 5)}", (30, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
                
                #cv2.putText(image, f"VER: {round(S_V, 5)}", (30, 380), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
                text_content +=f"HER: {round(S, 3)}\n"
                text_content +=f"VER: {round(S_V, 3)}\n"
                '''cv2.putText(image, f"{int(dist_right_lateral)}px", right_lateral_canthus_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 1)
                cv2.putText(image, f"{int(dist_right_medial)}px", right_medial_canthus_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 255), 1)
                cv2.putText(image, f"{int(dist_left_lateral)}px", left_lateral_canthus_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 1)
                cv2.putText(image, f"{int(dist_left_medial)}px", left_medial_canthus_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 255), 1)
                cv2.putText(image, f"{int(dist_rv_top_coords)}px", rv_top_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 1)
                cv2.putText(image, f"{int(dist_rv_bottom_coords)}px", rv_bottom_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 1)
                cv2.putText(image, f"{int(dist_lv_top_coords)}px", lv_top_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 1)
                cv2.putText(image, f"{int(dist_lv_bottom_coords)}px", lv_bottom_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 1)'''
                cv2.putText(image, "L", (lv_bottom_coords[0],lv_bottom_coords[1]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 3)
                cv2.putText(image, "R", (rv_bottom_coords[0],rv_bottom_coords[1]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 3)
                

    # Save the processed image
    cv2.imwrite(processed_path, image)
    crop_eyes_from_image(processed_path)
    # Create text file with details
    text_filename = processed_filename.replace(".jpg", ".txt").replace(".png", ".txt")
    print(f"Text file name: {text_filename}")
    text_path = os.path.join(PreliminaryResults_Folder, text_filename)

    print(f"Processed image saved as {processed_path}.")
    # Write the text to the file
    try:
        with open(text_path, "w") as file:
            file.write(text_content)
            print(f"Report successfully created and saved at: {text_path}")
    except Exception as e:
        print(f"An error occurred while creating the report: {e}")

    return image, text_content,text_filename




        