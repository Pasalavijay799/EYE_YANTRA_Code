import cv2
import numpy as np
import os

def create_combined_image(person_name, output_folder):
    processed_folder = os.path.join(output_folder, f"{person_name}_Areal")
    image_files = sorted([f for f in os.listdir(processed_folder) if f.startswith("gaze_") and f.endswith(".jpg")])

    if len(image_files) < 9:
        print(f"❌ Only {len(image_files)} images found. Skipping combined image.")
        return None

    images = [cv2.imread(os.path.join(processed_folder, img)) for img in image_files]

    # Resize all images to the same size (assuming the first image as reference)
    height, width = images[0].shape[:2]
    images_resized = [cv2.resize(img, (width, height)) for img in images]

    # Arrange images in a 3x3 grid
    row1 = np.hstack(images_resized[:3])
    row2 = np.hstack(images_resized[3:6])
    row3 = np.hstack(images_resized[6:9])
    combined_image = np.vstack([row1, row2, row3])

    combined_image_path = os.path.join(processed_folder, "combined_9gaze.jpg")
    cv2.imwrite(combined_image_path, combined_image)
    
    return "combined_9gaze.jpg"
