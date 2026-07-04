# import cv2
# import mediapipe as mp
# import numpy as np

# mp_face_mesh = mp.solutions.face_mesh

# # Indices for iris and eye corners from MediaPipe
# LEFT_IRIS = [474, 475, 476, 477]
# RIGHT_IRIS = [469, 470, 471, 472]
# RIGHT_EYE_CORNERS= [33, 133]     # Left: [Medial, Lateral]
# LEFT_EYE_CORNERS  = [362, 263]   # Right: [Medial, Lateral]

# def get_iris_center(landmarks, indices, image_shape):
#     h, w = image_shape[:2]
#     points = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices])
#     center = points.mean(axis=0)
#     return center

# def get_midpoint(landmarks, index1, index2, image_shape):
#     h, w = image_shape[:2]
#     x1, y1 = int(landmarks[index1].x * w), int(landmarks[index1].y * h)
#     x2, y2 = int(landmarks[index2].x * w), int(landmarks[index2].y * h)
#     return ((x1 + x2) / 2, (y1 + y2) / 2)

# def compute_horizontal_deviation(image_path):
#     image = cv2.imread(image_path)
#     if image is None:
#         print(f"Error loading image: {image_path}")
#         return None

#     with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
#         rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#         results = face_mesh.process(rgb)

#         if not results.multi_face_landmarks:
#             print(f"No face detected in {image_path}")
#             return None

#         landmarks = results.multi_face_landmarks[0].landmark

#         # Left eye
#         iris_l = get_iris_center(landmarks, LEFT_IRIS, image.shape)
#         midpoint_l = get_midpoint(landmarks, *LEFT_EYE_CORNERS, image.shape)
#         hd_left = iris_l[0] - midpoint_l[0]

#         # Right eye
#         iris_r = get_iris_center(landmarks, RIGHT_IRIS, image.shape)
#         midpoint_r = get_midpoint(landmarks, *RIGHT_EYE_CORNERS, image.shape)
#         hd_right = iris_r[0] - midpoint_r[0]

#         avg_hd = (abs(hd_left) + abs(hd_right)) / 2
#         return avg_hd

# def classify_pattern(hd_up, hd_primary, hd_down):
#     delta_up = hd_up - hd_primary
#     delta_down = hd_down - hd_primary

#     print(f"\nΔup: {delta_up:.2f}, Δdown: {delta_down:.2f}")

#     if abs(delta_up - delta_down) >= 0.5:
#         if delta_up > delta_down:
#             return "V-pattern"
#         else:
#             return "A-pattern"
#     elif delta_up > 1 and abs(delta_down) < 0.5:
#         return "Y-pattern"
#     elif delta_down < -0.8 and abs(delta_up) > 0.5:
#         return "Arrow-pattern"
#     elif abs(delta_up) < 0.5 and delta_down > 1:
#         return "λ-pattern (Lambda)"
#     elif delta_up > 10 and delta_down > 10:
#         return "X-pattern"
#     elif delta_up < -1 and delta_down < -1:
#         return "<>-pattern (Diamond)"
#     else:
#         return "No significant pattern"

# def main():
#     images = {
#         'upgaze': r"C:\Users\Karri\Documents\X_Swap\swapped_upper.jpg",
#         'primary': r"C:\Users\Karri\Documents\X_Swap\swapped_middle.jpg",
#         'downgaze': r"C:\Users\Karri\Documents\X_Swap\swapped_down.jpg"
#     }

#     deviations = {}
#     for gaze, path in images.items():
#         print(f"Processing {gaze}...")
#         hd = compute_horizontal_deviation(path)
#         if hd is not None:
#             deviations[gaze] = hd
#             print(f"{gaze} HD: {hd:.2f}")
#         else:
#             return

#     pattern = classify_pattern(deviations['upgaze'], deviations['primary'], deviations['downgaze'])
#     print(f"\n🧠 Detected Pattern: {pattern}")

# if __name__ == "__main__":
#     main()




import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

# Indices for iris and eye corners from MediaPipe
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
RIGHT_EYE_CORNERS = [33, 133]
LEFT_EYE_CORNERS = [362, 263]

def get_iris_center(landmarks, indices, image_shape):
    h, w = image_shape[:2]
    points = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices])
    center = points.mean(axis=0)
    return center

def get_midpoint(landmarks, index1, index2, image_shape):
    h, w = image_shape[:2]
    x1, y1 = int(landmarks[index1].x * w), int(landmarks[index1].y * h)
    x2, y2 = int(landmarks[index2].x * w), int(landmarks[index2].y * h)
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def compute_horizontal_deviation_and_center(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error loading image: {image_path}")
        return None, None

    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            print(f"No face detected in {image_path}")
            return None, None

        landmarks = results.multi_face_landmarks[0].landmark

        # Left eye
        iris_l = get_iris_center(landmarks, LEFT_IRIS, image.shape)
        midpoint_l = get_midpoint(landmarks, *LEFT_EYE_CORNERS, image.shape)
        hd_left = iris_l[0] - midpoint_l[0]

        # Right eye
        iris_r = get_iris_center(landmarks, RIGHT_IRIS, image.shape)
        midpoint_r = get_midpoint(landmarks, *RIGHT_EYE_CORNERS, image.shape)
        hd_right = iris_r[0] - midpoint_r[0]

        avg_hd = (abs(hd_left) + abs(hd_right)) / 2

        # Average iris center
        avg_iris_center = ((iris_l[0] + iris_r[0]) / 2, (iris_l[1] + iris_r[1]) / 2)

        return avg_hd, avg_iris_center

def classify_pattern(hd_up, hd_primary, hd_down):
    delta_up = hd_up - hd_primary
    delta_down = hd_down - hd_primary

    print(f"\nΔup: {delta_up:.2f}, Δdown: {delta_down:.2f}")

    if abs(delta_up - delta_down) >= 0.5:
        if delta_up > delta_down:
            return "V-pattern"
        else:
            return "A-pattern"
    elif delta_up > 1 and abs(delta_down) < 0.5:
        return "Y-pattern"
    elif delta_down < -0.8 and abs(delta_up) > 0.5:
        return "Arrow-pattern"
    elif abs(delta_up) < 0.5 and delta_down > 1:
        return "λ-pattern (Lambda)"
    elif delta_up > 10 and delta_down > 10:
        return "X-pattern"
    elif delta_up < -1 and delta_down < -1:
        return "<>-pattern (Diamond)"
    else:
        return "No significant pattern"

def visualize_iris_path(centers_dict, canvas_size=(500, 500)):
    canvas = np.ones((canvas_size[1], canvas_size[0], 3), dtype=np.uint8) * 255

    # Normalize and map all centers to canvas
    all_x = [c[0] for c in centers_dict.values()]
    all_y = [c[1] for c in centers_dict.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    def map_to_canvas(pt):
        x = int((pt[0] - min_x) / (max_x - min_x + 1e-5) * (canvas_size[0] - 100)) + 50
        y = int((pt[1] - min_y) / (max_y - min_y + 1e-5) * (canvas_size[1] - 100)) + 50
        return (x, y)

    # Draw points and lines
    colors = {"upgaze": (255, 0, 0), "primary": (0, 255, 0), "downgaze": (0, 0, 255)}
    gaze_order = ["upgaze", "primary", "downgaze"]
    prev_pt = None
    for gaze in gaze_order:
        pt = map_to_canvas(centers_dict[gaze])
        cv2.circle(canvas, pt, 8, colors[gaze], -1)
        cv2.putText(canvas, gaze, (pt[0] + 5, pt[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[gaze], 1)
        if prev_pt is not None:
            cv2.line(canvas, prev_pt, pt, (0, 0, 0), 2)
        prev_pt = pt

    return canvas

def main():
    images = {
        'upgaze': r"C:\Users\Karri\Documents\V_Swap\swapped_upper.jpg",
        'primary': r"C:\Users\Karri\Documents\V_Swap\swapped_middle.jpg",
        'downgaze': r"C:\Users\Karri\Documents\V_Swap\swapped_down.jpg"
    }

    deviations = {}
    left_iris_pts = []
    right_iris_pts = []

    for gaze, path in images.items():
        print(f"Processing {gaze}...")
        image = cv2.imread(path)
        if image is None:
            print(f"Error loading image: {path}")
            return

        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                print(f"No face detected in {path}")
                return

            landmarks = results.multi_face_landmarks[0].landmark

            # Left eye
            iris_l = get_iris_center(landmarks, LEFT_IRIS, image.shape)
            midpoint_l = get_midpoint(landmarks, *LEFT_EYE_CORNERS, image.shape)
            hd_left = iris_l[0] - midpoint_l[0]

            # Right eye
            iris_r = get_iris_center(landmarks, RIGHT_IRIS, image.shape)
            midpoint_r = get_midpoint(landmarks, *RIGHT_EYE_CORNERS, image.shape)
            hd_right = iris_r[0] - midpoint_r[0]

            # Average HD
            avg_hd = (abs(hd_left) + abs(hd_right)) / 2
            deviations[gaze] = avg_hd

            # Store iris centers for path plotting
            left_iris_pts.append(iris_l)
            right_iris_pts.append(iris_r)

            print(f"{gaze} HD: {avg_hd:.2f}")

    # Pattern classification
    pattern = classify_pattern(deviations['upgaze'], deviations['primary'], deviations['downgaze'])
    print(f"\n🧠 Detected Pattern: {pattern}")

    # Draw and save iris movement paths
    draw_iris_paths(left_iris_pts, right_iris_pts)

    
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def draw_iris_paths(left_iris_points, right_iris_points, save_path="iris_path_plot.jpg"):
    canvas = np.ones((500, 800, 3), dtype=np.uint8) * 255  # White canvas
    gaze_labels = ['Upgaze', 'Primary', 'Downgaze']
    colors = {'left': (0, 0, 255), 'right': (0, 255, 0)}  # BGR: Red for left, Green for right

    # Normalize and scale points to fit canvas
    all_points = np.array(left_iris_points + right_iris_points)
    min_x, min_y = np.min(all_points, axis=0)
    max_x, max_y = np.max(all_points, axis=0)
    scale_x = 700 / (max_x - min_x + 1e-6)
    scale_y = 400 / (max_y - min_y + 1e-6)

    def scale(pt):
        x = int((pt[0] - min_x) * scale_x + 50)
        y = int((pt[1] - min_y) * scale_y + 50)
        return (x, y)

    # Draw paths
    for points, label, color in zip([left_iris_points, right_iris_points], ['Left Eye', 'Right Eye'], [colors['left'], colors['right']]):
        scaled_points = [scale(pt) for pt in points]
        for i in range(len(scaled_points)-1):
            cv2.line(canvas, scaled_points[i], scaled_points[i+1], color, 2)
        for i, pt in enumerate(scaled_points):
            cv2.circle(canvas, pt, 5, color, -1)
            cv2.putText(canvas, gaze_labels[i], (pt[0]+5, pt[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.putText(canvas, "Left Eye Path (Red)", (50, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors['left'], 2)
    cv2.putText(canvas, "Right Eye Path (Green)", (400, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors['right'], 2)

    cv2.imwrite(save_path, canvas)
    print(f"\n🖼️ Path image saved as: {save_path}")

if __name__ == "__main__":
    main()
