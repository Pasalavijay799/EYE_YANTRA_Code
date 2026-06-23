import cv2
import os
import numpy as np
import mediapipe as mp
import math
from crop_eyes_from_image import crop_eyes_from_image
# Initialize MediaPipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True, max_num_faces=1)

# Define corneal reflection landmark indices (approximate)
LEFT_PUPIL = [469, 470, 471, 472]  # Mediapipe iris landmarks
RIGHT_PUPIL = [474, 475, 476, 477]


#start of functions in hirschberg function
# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh

# Define constants
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_IRIS = [469, 470, 471, 472]
RIGHT_IRIS = [474, 475, 476, 477]

# Function to calculate Euclidean distance
def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# Function to calculate the centroid of a contour
def calculate_centroid(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return (0, 0)
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)



# Function to divide line with dots
def divide_line_with_dots(image, point1, point2, num_segments=6, line_color=(0, 255, 0), dot_color=(0, 0, 255), dot_radius=1, thickness=2):
    cv2.line(image, point1, point2, line_color, thickness)
    division_points = []
    for i in range(num_segments + 1):
        x = point1[0] + i * (point2[0] - point1[0]) // num_segments
        y = point1[1] + i * (point2[1] - point1[1]) // num_segments
        division_points.append((x, y))
        cv2.circle(image, (x, y), dot_radius, dot_color, -1)
    distance = euclidean_distance(division_points[0], division_points[1])
    return distance


def mark_iris_with_text(frame, iris_center, iris_side):
    cv2.putText(frame, iris_side, (iris_center[0] - 10, iris_center[1] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)


# Function to determine the position of a point relative to a reference point
def find_point_position(reference, point):
    x_diff = point[0] - reference[0]
    y_diff = point[1] - reference[1]
    
    horizontal = "right" if x_diff > 0 else "left"
    vertical = "below" if y_diff > 0 else "above"
    horizontal_distance = abs(x_diff)
    vertical_distance = abs(y_diff)
    
    return horizontal, vertical, horizontal_distance, vertical_distance





def calculate_strabismus_angle(X1, Y1, M1, N1, X2, Y2, M2, N2, lamp_distance=0.33):
    """
    Angle-based calculation for strabismus detection and classification.

    Parameters:
    X1, Y1, M1, N1: Right eye center (X1, Y1), bright spot (M1, N1).
    X2, Y2, M2, N2: Left eye center (X2, Y2), bright spot (M2, N2).
    lamp_distance: Distance of the pupil lamp from the patient in meters (default = 0.33 m).

    Returns:
    Dict containing angular deviations, affected eye, and strabismus type.
    """
    def calculate_angle(H, V, D):
        # Horizontal and vertical angles in radians
        theta_H = math.atan(H / D)
        theta_V = math.atan(V / D)
        # Convert to degrees
        theta_H_deg = math.degrees(theta_H)
        theta_V_deg = math.degrees(theta_V)
        return theta_H_deg, theta_V_deg

    # Step 1: Horizontal and vertical distances
    H1 = abs(X1 - M1)
    V1 = abs(Y1 - N1)
    H2 = abs(X2 - M2)
    V2 = abs(Y2 - N2)
    
    # Step 2: Angular deviation for both eyes
    theta_H1, theta_V1 = calculate_angle(H1, V1, lamp_distance)
    theta_H2, theta_V2 = calculate_angle(H2, V2, lamp_distance)
    
    # Step 3: Angular deviations between eyes
    delta_theta_H = abs(theta_H1 - theta_H2)
    delta_theta_V = abs(theta_V1 - theta_V2)
    
    # Step 4: Threshold for strabismus (e.g., ~1 mm = 7.5° deflection)
    strabismus_threshold = 7.5  # degrees

    # Step 5: Determine if strabismus exists
    if delta_theta_H <= strabismus_threshold and delta_theta_V <= strabismus_threshold:
        return {
            "Horizontal Angle (Right Eye)": theta_H1,
            "Vertical Angle (Right Eye)": theta_V1,
            "Horizontal Angle (Left Eye)": theta_H2,
            "Vertical Angle (Left Eye)": theta_V2,
            "status": "Normal",
            "strabismus_eye": None,
            "strabismus_type": None
        }
    
    # Step 6: Determine the strabismus eye and type
    strabismus_eye = None
    strabismus_type = None
    
    if delta_theta_H > strabismus_threshold:
        if theta_H1 > theta_H2:
            strabismus_eye = "Right Eye"
            strabismus_type = "Esotropia (Inward)" if X1 - M1 > 0 else "Exotropia (Outward)"
        else:
            strabismus_eye = "Left Eye"
            strabismus_type = "Esotropia (Inward)" if X2 - M2 > 0 else "Exotropia (Outward)"
    
    if delta_theta_V > strabismus_threshold:
        if theta_V1 > theta_V2:
            strabismus_eye = "Right Eye" if not strabismus_eye else strabismus_eye
            strabismus_type = strabismus_type or ("Hypertropia (Upward)" if Y1 - N1 < 0 else "Hypotropia (Downward)")
        else:
            strabismus_eye = "Left Eye" if not strabismus_eye else strabismus_eye
            strabismus_type = strabismus_type or ("Hypertropia (Upward)" if Y2 - N2 < 0 else "Hypotropia (Downward)")
    
    return {
        "Horizontal Angle (Right Eye)": theta_H1,
        "Vertical Angle (Right Eye)": theta_V1,
        "Horizontal Angle (Left Eye)": theta_H2,
        "Vertical Angle (Left Eye)": theta_V2,
        "status": "Strabismus Detected",
        "strabismus_eye": strabismus_eye,
        "strabismus_type": strabismus_type
    }

  





def analyze_hirschberg(image, results_folder, filename):
    """
    Analyzes corneal reflections using the Hirschberg test.
    
    - Detects pupil positions
    - Checks light reflex positions
    - Determines potential squint (strabismus) angles
    
    Returns processed image path and text analysis results.
    """
    text_content = f"Hirschberg Analysis Report\n\n"
    text_content += f"Input Image Path: {filename}\n"


    # Convert image to RGB (required for MediaPipe)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_rgb=rgb_image.copy()
    
    
    # Process the image with Face Mesh
    with mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True) as face_mesh:
        results = face_mesh.process(img_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                img_h, img_w, _ = image.shape

                # Extract and convert landmarks
                left_eye_coords = [(int(face_landmarks.landmark[i].x * img_w), int(face_landmarks.landmark[i].y * img_h)) for i in LEFT_EYE]
                right_eye_coords = [(int(face_landmarks.landmark[i].x * img_w), int(face_landmarks.landmark[i].y * img_h)) for i in RIGHT_EYE]
                left_iris_coords = [(int(face_landmarks.landmark[i].x * img_w), int(face_landmarks.landmark[i].y * img_h)) for i in LEFT_IRIS]
                right_iris_coords = [(int(face_landmarks.landmark[i].x * img_w), int(face_landmarks.landmark[i].y * img_h)) for i in RIGHT_IRIS]

                # Draw eye contours
                ##cv2.polylines(image, [np.array(left_eye_coords, np.int32)], isClosed=True, color=(255, 0, 0), thickness=1)
                ##cv2.polylines(image, [np.array(right_eye_coords, np.int32)], isClosed=True, color=(0, 255, 0), thickness=1)

                # Draw iris circles
                (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(np.array(left_iris_coords))
                (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(np.array(right_iris_coords))
                l_center, r_center = (int(l_cx), int(l_cy)), (int(r_cx), int(r_cy))
                ##cv2.circle(image, l_center, int(l_radius), (255, 0, 0), 1)
                ##cv2.circle(image, r_center, int(r_radius), (0, 255, 0), 1)

                
                def calculate_center(rect):
                    x, y, w, h = rect
                    return (x + w // 2, y + h // 2)
                frame=image
                left_eye_rect = cv2.boundingRect(np.array(left_eye_coords, np.int32))
                right_eye_rect = cv2.boundingRect(np.array(right_eye_coords, np.int32))
                left_eye_center = calculate_center(left_eye_rect)
                right_eye_center = calculate_center(right_eye_rect)
                l_cx=((left_iris_coords[1][0] +left_iris_coords[3][0])/2)
                l_cy=((left_iris_coords[1][1] +left_iris_coords[3][1])/2)
                r_cx=((right_iris_coords[1][0] +right_iris_coords[3][0])/2)
                r_cy=((right_iris_coords[1][1] +right_iris_coords[3][1])/2)
                left_iris_center = (int(l_cx), int(l_cy))
                right_iris_center = (int(r_cx), int(r_cy))
                
                # Draw centers of the rectangles and irises
                #cv2.circle(frame, left_eye_center, 3, (255, 0, 0), -1)  # Blue for left eye center
                #cv2.circle(frame, right_eye_center, 3, (0, 255, 0), -1)  # Green for right eye center
                #cv2.circle(frame, left_iris_center, 3, (255, 0, 0), -1)  # Blue for left iris center
                #cv2.circle(frame, right_iris_center, 3, (0, 255, 0), -1)  # Green for right iris center
                print("left_eye_center:",left_eye_center,"left_iris_center:",left_iris_center)
                print("right_eye_center:",right_eye_center,"right_iris_center:",right_iris_center)

                left_distance_cm = (euclidean_distance(left_eye_center, left_iris_center))
                right_distance_cm = (euclidean_distance(right_eye_center, right_iris_center))

                # Display distances on the frame
                ##cv2.putText(frame, f"Left Eye cntr to Iris cntr: {left_distance_cm:.3f} px", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                ##cv2.putText(frame, f"Right Eye Cntr to Iris cntr: {right_distance_cm:.3f} px", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

                # Calculate distance to detected white spots
                lhd=0
                lvd=0
                rhd=0
                rvd=0
                #Create a mask for the iris region
                iris_mask = np.zeros((img_h, img_w), dtype=np.uint8)
                cv2.fillPoly(iris_mask, [np.array(left_iris_coords, dtype=np.int32)], 255)
                cv2.fillPoly(iris_mask, [np.array(right_iris_coords, dtype=np.int32)], 255)

                # Mask the iris regions in the frame
                iris_only = cv2.bitwise_and(frame, frame, mask=iris_mask)

                # Convert the iris region to grayscale to detect white areas
                gray_iris = cv2.cvtColor(iris_only, cv2.COLOR_BGR2GRAY)
                white_areas = cv2.inRange(gray_iris,150, 255)

                # Highlight the detected white areas with a different color (e.g., red)
                #frame[white_areas ] = [255, 0, 255]  # Mark white areas with red

                # Find contours in the white areas to locate the white spots
                contours, _ = cv2.findContours(white_areas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                '''if not contours:
                	cv2.putText(image, "Reflex Light Not Detected", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                	cv2.putText(image, "Slightly vary Threshhold /Upload New image light on image properly", (6, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)'''
                # Draw lines on the iris
                lv = divide_line_with_dots(image, left_iris_coords[1], left_iris_coords[3])
                lh = divide_line_with_dots(image, left_iris_coords[0], left_iris_coords[2])
                rv = divide_line_with_dots(image, right_iris_coords[1], right_iris_coords[3])
                rh = divide_line_with_dots(image, right_iris_coords[0], right_iris_coords[2])

                mark_iris_with_text(frame, r_center, 'R')
                mark_iris_with_text(frame, l_center, 'L')
                # Add text for measurements
                #cv2.putText(image, f"lv: {lv:.2f}px lh: {lh:.2f}px rv: {rv:.2f}px rh: {rh:.2f}px", (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                text_content += f"lv: {lv:.2f}px \nlh: {lh:.2f}px \nrv: {rv:.2f}px \nrh: {rh:.2f}px\n"
                # Calculate distances from the center of the pupil to the white spots
                def calculate_center(rect):
                    x, y, w, h = rect
                    return (x + w // 2, y + h // 2)
                
                Flag= False
                (M1,N1)=(0,0)
                (M2,N2)=(0,0)
                area=0
                prev_areaR=[]
                prev_areaL=[]
                MLD=0
                MRD=0
                lhd=0
                rhd=0
                rvd=0
                lvd=0
                radiusL=0
                radiusR=0
                for contour in contours:
                    # Calculate the centroid of the current contour
                    centroid = calculate_centroid(contour)
                    x, y = centroid
                    

                    print(x,y)
                    #cv2.drawContours(frame, [contour], -1, (255, 255, 0), 20)  # Green contour with thickness 3
                    (x_cen, y_cen), radius = cv2.minEnclosingCircle(contour)
                    center = (int(x), int(y))
                    radius = int(radius)
                    # Draw the circle around the contour
                    ##cv2.circle(image, center, 10, (255, 255, 0), -1)  # Green circle with thickness 2
                    # Calculate distances to the left and right iris centers
                    distance_to_left_iris = euclidean_distance(left_iris_center, (x, y))
                    distance_to_right_iris = euclidean_distance(right_iris_center, (x, y))
                    print("distance :l",distance_to_left_iris)
                    print("distance :r",distance_to_right_iris)
                    # Determine which iris is closer and display the distance 
                    area = cv2.contourArea(contour)
                    print(area)
                    if distance_to_left_iris < distance_to_right_iris and distance_to_left_iris<=20 :
                        #distance_to_white_spot_cm = pixel_to_cm(distance_to_left_iris)
                        Flag= True
                        print(area)
                        prev_areaL.append(area)
                        print(prev_areaL)
                        print("max area",max(prev_areaL))
                        
                        
                        if(abs((x-left_iris_center[0])/lh) <=1 and area>=max(prev_areaL)):
                            lhd=15
                            
                        elif(abs((x-left_iris_center[0])/lh) >1 and abs((x-left_iris_center[0])/lh) <=2  and area >=max(prev_areaL)):
                            lhd=30
                        elif abs((x - left_iris_center[0]) / lh) > 2 and abs((x - left_iris_center[0]) / lh) <= 3 and area >= max(prev_areaL):
                            lhd=45
                        if(abs((y-left_iris_center[1])/lv) <=1 )  and area>min(prev_areaL):
                            lvd=15
                        elif(abs((y-left_iris_center[1])/lv) >1 and abs((y-left_iris_center[1])/lv) <=2  and area>=max(prev_areaL)):
                            lvd=30
                        elif(abs((y-left_iris_center[1])/lv) >2 and abs((y-left_iris_center[1])/lv) <=3  and area>=min(prev_areaL)):
                            lvd=45
                        if  area>=max(prev_areaL):
                            lhd=abs((x-left_iris_center[0])/lh*15)
                            lvd=abs((y-left_iris_center[1])/lv*15)
                            (M2,N2)=(x,y)
                            radiusL=radius
                            MLD=distance_to_left_iris
                            print("lhd ,lvd",lhd,lvd)
                            ##cv2.putText(frame, f"Left Iris White Spot from center: {distance_to_left_iris:.2f} px", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        '''horizontal, vertical, horizontal_distance, vertical_distance=find_point_position(left_iris_center, (x, y ))
                        print(f"LEFT EYE Point ({x}, {y}) is to the {horizontal} ({horizontal_distance} pixels) and {vertical} ({vertical_distance} pixels) of the reference point {left_iris_center}.")
                        
                        if(horizontal=="left" and horizontal_distance<vertical_distance):
                            print("LEFT Eye likely Esotropia")
                            cv2.putText(frame, "Left Eye likely  Esotropia", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(horizontal=="right" and horizontal_distance<vertical_distance):
                            print("LEFT Eye likely Exotropia")
                            cv2.putText(frame, "Left Eye likely  Exotropia", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(vertical=="above" and horizontal_distance>vertical_distance):
                            print("LEFT Eye likely hypotropia")
                            cv2.putText(frame, "Left Eye likely hypotropia", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(vertical=="below" and horizontal_distance>vertical_distance):
                            print("LEFT Eye likely hypertropia")
                            cv2.putText(frame, "Left Eye likely hypertropia", (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)'''
                        
                        
                    
                    elif distance_to_left_iris > distance_to_right_iris and distance_to_right_iris<=20:
                        prev_areaR.append(area)
                        
                        #distance_to_white_spot_cm = pixel_to_cm(distance_to_right_iris)
                        
                        Flag= True
                        if(abs((x-right_iris_center[0])/rh) <=1) and area >=max(prev_areaR):
                            rhd=15
                        elif(abs((x-right_iris_center[0])/rh) >1 and abs((x-right_iris_center[0])/rh) <=2) and area >=max(prev_areaR):
                            rhd=30
                        elif(abs((x-left_iris_center[0])/rh) >2 and abs((x-right_iris_center[0])/rh) <=3) and area >=max(prev_areaR):
                            rhd=45
                        if(abs((y-right_iris_center[1])/rv) <=1) and area >=max(prev_areaR):
                            rvd=15
                        elif(abs((y-right_iris_center[1])/rv) >1 and abs((y-right_iris_center[1])/rv) <=2) and area >=max(prev_areaR):
                            rvd=30
                        elif(abs((y-right_iris_center[1])/rv) >2 and abs((y-right_iris_center[1])/rv) <=3) and area >=max(prev_areaR):
                            rvd=45
                        if area >=max(prev_areaR):
                            rhd=abs((x-right_iris_center[0])/rh*15)
                            rvd=abs((y-right_iris_center[1])/rv*15)
                            (M1,N1)=(x,y)
                            radiusR=radius
                            print("rhd ,rvd",rhd,rvd)
                            MRD=distance_to_right_iris
                        
                        '''horizontal, vertical, horizontal_distance, vertical_distance=find_point_position(right_iris_center, (x, y ))
                        print(f"RIGHT EYE Point ({x}, {y}) is to the {horizontal} ({horizontal_distance} pixels) and {vertical} ({vertical_distance} pixels) of the reference point {right_iris_center}.")
                        if(horizontal=="left" and horizontal_distance<vertical_distance):
                            print("Right Eye likely Esotropia")
                            cv2.putText(frame, "Right Eye likely Esotropia", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(horizontal=="right" and horizontal_distance<vertical_distance):
                            print("Right Eye likely Exotropia")
                            cv2.putText(frame, "Right Eye likely Exotropia", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(vertical=="above" and horizontal_distance>vertical_distance):
                            print("Right Eye likely hypotropia")
                            cv2.putText(frame, "Right Eye likely hypertropia", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        elif(vertical=="below" and horizontal_distance>vertical_distance):
                            print("Right Eye likely hypertropia")
                            cv2.putText(frame, "Right Eye likely hypertropia", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)'''
                
                
                
                
                #cv2.putText(frame, f"Left Iris White Spot from center: {MLD:.2f} px", (10, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                #cv2.putText(frame, f"Right Iris White Spot: {MRD:.2f} px", (10, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                text_content += f"Left Iris White Spot from center: {MLD:.2f} px\n"
                text_content += f"Right Iris White Spot: {MRD:.2f} px\n"
                
                if Flag:
                    result = calculate_strabismus_angle(X1=right_iris_center[0], Y1=right_iris_center[1], M1=M1,N1=N1, X2=left_iris_center[0], Y2=left_iris_center[1],  M2=M2, N2=N2)
                    print(result)
                    cv2.circle(image, (M1,N1), radiusR+1, (255, 255, 0), 2)  # Green circle with thickness 2
                    cv2.circle(image, (M2,N2), radiusL+1, (255, 255, 0), 2)
                    
                    if result["status"] == "Strabismus Detected" and (rvd>=15 or lvd >=15 or rhd>=15 or lhd>=15) :
                        strabismus_eye = result['strabismus_eye']
                        strabismus_type = result['strabismus_type']
                        # Display the affected eye and type
                        print(f"Strabismus detected in {strabismus_eye} with type: {strabismus_type}.")
                        #cv2.putText(frame, f"Strabismus detected in {strabismus_eye}", (10, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        #cv2.putText(frame, f"Type: {strabismus_type}", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        
                        text_content += f"Strabismus detected in {strabismus_eye} with type: {strabismus_type}.\n"
                        text_content += f"Type: {strabismus_type}:"
                		
                		# Specific feedback based on the eye and type
                        if strabismus_eye == "Left Eye":
                            if strabismus_type == "Esotropia (Inward)":
                                print("LEFT Eye likely Esotropia")
                                #cv2.putText(frame, "Left Eye likely Esotropia", (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                text_content += "Left Eye likely Esotropia"
                            elif strabismus_type == "Exotropia (Outward)":
                                print("LEFT Eye likely Exotropia")
                                #cv2.putText(frame, "Left Eye likely Exotropia", (10, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                text_content += "Left Eye likely Exotropia"
                            elif strabismus_type == "Hypertropia (Upward)":
                                print("LEFT Eye likely Hypertropia")
                                #cv2.putText(frame, "Left Eye likely Hypertropia", (10,500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                text_content += "Left Eye likely Hypertropia"
                            elif strabismus_type == "Hypotropia (Downward)":
                                print("LEFT Eye likely Hypotropia")
                                #cv2.putText(frame, "Left Eye likely Hypotropia", (10,500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                text_content += "Left Eye likely Hypotropia"
                        elif strabismus_eye == "Right Eye":
                            if strabismus_type == "Esotropia (Inward)":
                                print("RIGHT Eye likely Esotropia")
                                #cv2.putText(frame, "Right Eye likely Esotropia", (10, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                text_content += "Right Eye likely Esotropia"
                            elif strabismus_type == "Exotropia (Outward)":
                                print("RIGHT Eye likely Exotropia")
                                #cv2.putText(frame, "Right Eye likely Exotropia", (10, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                text_content += "Right Eye likely Exotropia"
                            elif strabismus_type == "Hypertropia (Upward)":
                                print("RIGHT Eye likely Hypertropia")
                                #cv2.putText(frame, "Right Eye likely Hypertropia", (10, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                text_content += "Right Eye likely Hypertropia"
                            elif strabismus_type == "Hypotropia (Downward)":
                                print("RIGHT Eye likely Hypotropia")
                                #cv2.putText(frame, "Right Eye likely Hypotropia", (10,520), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                text_content += "Right Eye likely Hypotropia"
                    else:
                        # If no strabismus is detected
                        print("No strabismus detected.")
                        #cv2.putText(frame, "No Strabismus Detected", (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        text_content += "No Strabismus Detected"

                        
                    #cv2.putText(frame, f"lvd: {lvd} deg ,lhd: {lhd} deg ", (10, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    #cv2.putText(frame, f"rvd: {rvd} deg ,rhd: {rhd} deg ", (10, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    text_content += f"\n \nrvd: {rvd:.3f} deg \nrhd: {rhd:.3f} deg\n "
                    text_content += f"\n \nlvd: {lvd:.3f} deg \nlhd: {lhd:.3f} deg \n "
                    
                else:
                    #cv2.putText(image, "Reflex Light Not Detected", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    #cv2.putText(image, "Slightly vary Threshhold /Upload New image light on image properly", (6, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    text_content += f"\n \nReflex Light Not Detected\n "
                
                # Save processed image
                processed_filename = f"processed_{filename}"
                processed_path = os.path.join(results_folder, processed_filename)
                cv2.imwrite(processed_path, image)
                #cropping
                crop_eyes_from_image(processed_path)


    # Create text report
    text_filename = processed_filename.replace(".jpg", ".txt").replace(".png", ".txt")
    text_path = os.path.join(results_folder, text_filename)

    

    with open(text_path, "w", encoding="utf-8") as file:  # ✅ Force UTF-8 encoding
        file.write(text_content)


    print(f"Processed image saved as: {processed_filename}")
    print(f"Text report saved as: {text_filename}")
    return processed_filename, text_content, text_filename
