from eye_detection import check_eye_status

# Test with an image
#image_path = r"/home/teja/Documents/iittp_project/Eye Yantra(1)/JSR_Strabismus_Bluetooth_WiFi_Interface_Tests/9GazeTestImages/teja3/gaze_2.jpg"  # Change this to the actual image path
for i in range(1,10):
	# Test with an image
	image_path = f"/home/teja/Documents/iittp_project/Eye Yantra(1)/JSR_Strabismus_Bluetooth_WiFi_Interface_Tests/9GazeTestImages/Govind sir/gaze_{i}.jpg"  # Change this to the actual image path
	result = check_eye_status(image_path)
	print(i, result)
