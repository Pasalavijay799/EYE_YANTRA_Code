# import cv2
# import numpy as np

# # Load images
# face_img = cv2.imread(r"C:\Users\Karri\Documents\WIN_20250514_17_53_54_Pro.jpg")
# new_eyes_img = cv2.imread(r'c:\Users\Karri\Documents\Pattern_Strabismus_Fig_2.jpg')

# clone = face_img.copy()
# refPt = []
# cropping = False

# def click_and_crop(event, x, y, flags, param):
#     global refPt, cropping, face_img

#     if event == cv2.EVENT_LBUTTONDOWN:
#         refPt = [(x, y)]
#         cropping = True

#     elif event == cv2.EVENT_LBUTTONUP:
#         refPt.append((x, y))
#         cropping = False

#         cv2.rectangle(face_img, refPt[0], refPt[1], (0, 255, 0), 2)
#         cv2.imshow("Select Eye Region", face_img)

# cv2.namedWindow("Select Eye Region")
# cv2.setMouseCallback("Select Eye Region", click_and_crop)

# print("[INFO] Draw a rectangle over the eye region, then press 'c' to confirm.")

# while True:
#     cv2.imshow("Select Eye Region", face_img)
#     key = cv2.waitKey(1) & 0xFF

#     if key == ord("r"):
#         face_img = clone.copy()

#     elif key == ord("c"):
#         break

# cv2.destroyAllWindows()

# # If 2 points are selected (rectangle), replace that region with resized eye image
# if len(refPt) == 2:
#     x1, y1 = refPt[0]
#     x2, y2 = refPt[1]

#     x_min, x_max = min(x1, x2), max(x1, x2)
#     y_min, y_max = min(y1, y2), max(y1, y2)

#     width = x_max - x_min
#     height = y_max - y_min

#     # Resize new eye image
#     resized_eyes = cv2.resize(new_eyes_img, (width, height))

#     # Replace region in face image
#     face_img[y_min:y_max, x_min:x_max] = resized_eyes

#     # Save and show result
#     cv2.imwrite("replaced_eyes_manual.jpg", face_img)
#     print("[INFO] Eyes replaced and saved to 'replaced_eyes_manual.jpg'")
#     cv2.imshow("Result", face_img)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
# else:
#     print("[ERROR] Region not selected properly.")












import cv2
import numpy as np
import os
from pathlib import Path

# Load original face image
face_img_path = r"C:\Users\Karri\Documents\WIN_20250514_17_53_54_Pro.jpg"
face_img_original = cv2.imread(face_img_path)

# Initialize variables
clone = face_img_original.copy()
refPt = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    global refPt, cropping, face_img_original

    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        refPt.append((x, y))
        cropping = False
        cv2.rectangle(face_img_original, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("Select Eye Region", face_img_original)

# Let user draw a rectangle around the eye region
cv2.namedWindow("Select Eye Region")
cv2.setMouseCallback("Select Eye Region", click_and_crop)

print("[INFO] Draw a rectangle over the eye region, then press 'c' to confirm.")
while True:
    cv2.imshow("Select Eye Region", face_img_original)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("r"):
        face_img_original = clone.copy()
    elif key == ord("c"):
        break
cv2.destroyAllWindows()

# Proceed only if the region was selected
if len(refPt) == 2:
    x1, y1 = refPt[0]
    x2, y2 = refPt[1]
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    width = x_max - x_min
    height = y_max - y_min

    # Input and output folders
    base_folders = ["X", "A", "V"]
    base_path = Path(r"C:\Users\Karri\Documents")

    for folder in base_folders:
        input_folder = base_path / folder
        output_folder = base_path / f"{folder}_Swap"
        output_folder.mkdir(exist_ok=True)

        for file_name in os.listdir(input_folder):
            file_path = input_folder / file_name
            if not file_path.is_file():
                continue

            # Read new eye image and resize
            new_eyes_img = cv2.imread(str(file_path))
            if new_eyes_img is None:
                print(f"[WARNING] Could not load image: {file_path}")
                continue

            resized_eyes = cv2.resize(new_eyes_img, (width, height))

            # Create a fresh copy of the original face image
            face_img = face_img_original.copy()
            face_img[y_min:y_max, x_min:x_max] = resized_eyes

            # Save result
            output_path = output_folder / f"swapped_{file_name}"
            cv2.imwrite(str(output_path), face_img)
            print(f"[INFO] Saved: {output_path}")

    print("[INFO] All images processed.")
else:
    print("[ERROR] Eye region not selected properly.")
