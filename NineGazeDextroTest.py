import cv2
from NineGazeDextro import EyeAnalyzer  # Make sure your class is saved in this file
from crop_eyes_from_image import crop_eyes_from_image

# Load image (replace with your image path)
image_path = r"/home/teja/Documents/iittp_project/Eye Yantra(1)/JSR_Strabismus_Bluetooth_WiFi_Interface_Tests/9GazeTestImages/Teja Kumar Narayana_12345678_2005-06-27/testing/gaze_7.jpg"
image = cv2.imread(image_path)

# if i in [3, 6, 9]:
#     gaze_dir = "dextro"
# elif i in [1, 4, 7]:
#     gaze_dir = "levo"
# else:
#     gaze_dir = "center"

if image is None:
    print("Failed to load image.")
else:
    analyzer = EyeAnalyzer()
    result = analyzer.process_frame(image, gaze_direction="levo")

    # Save or display the processed image
    cv2.imshow("Processed Frame", result["processed_frame"])
    cv2.imwrite("underaction_Levo_.jpg", result["processed_frame"])
    crop_eyes_from_image("underaction_Levo_.jpg")
    cv2.waitKey(0)

    
    cv2.destroyAllWindows()

    # Print computed distances
    print("\n--- Computed Distances ---")
    print(result)
    for key, val in result["distances"].items():
        print(f"{key}: {val:.2f}")

    # Print grades
    print("\n--- Grading Results ---")
    for key, val in result["grades"].items():
        print(f"{key}: Grade {val}")
