from overaction_Inferior_Dextro import EyeIrisDetector
import cv2

detector = EyeIrisDetector()
result_img = detector.run_on_image("9GazeTestImages\Govind sir\gaze_6.jpg", show=False)

# Save the result if needed
if result_img is not None:
    cv2.imwrite("overaction_grad_dextro.jpg", result_img)





# Import the class
from eye_overaction_detector import EyeIrisDetector

# Create instance for left eye (levo)
detector = EyeIrisDetector(mode='left')
detector.run_on_image("9GazeTestImages\Govind sir\gaze_1.jpg")

