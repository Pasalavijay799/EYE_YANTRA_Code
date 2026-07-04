import os
import cv2
from flask import render_template, session, redirect, url_for,flash
from eye_detection import check_eye_status  # Import eye detection function
from hirschberg_analysis import analyze_hirschberg  # Import Hirschberg-specific analysis
#from crop_eyes_from_image import crop_eyes_from_image
# Define folders (Update to match your storage structure)
HIRSCHBERG_FOLDER = "HirschbergTestImages"  # Updated storage location
HirschbergResults_Folder = "Hirschberg_Results"
if not os.path.exists(HirschbergResults_Folder):
    os.makedirs(HirschbergResults_Folder)
# def HirschbergShowResult():
#     try:
#         # Get the latest image
#         images = sorted(
#             [f for f in os.listdir(HIRSCHBERG_FOLDER) if f.endswith((".jpg", ".png"))],
#             key=lambda f: os.path.getmtime(os.path.join(HIRSCHBERG_FOLDER, f)),
#             reverse=True
#         )

#         if not images:
#             session["error_message"] = "❌ No images found. Please capture an image first."
#             return redirect(url_for("hirschberg_test"))

#         latest_image = images[0]
#         image_path = os.path.join(HIRSCHBERG_FOLDER, latest_image)

#         # Check eye status
#         eye_status = check_eye_status(image_path)
#         print(f"🔍 Eye status: {eye_status}")
#         if "⚠️" in eye_status:
#             flash(eye_status, "error")  # ✅ Use flash 
#             return redirect(url_for("hirschberg_test"))

#         # Load image
#         image = cv2.imread(image_path)
#         if image is None:
#             session["error_message"] = "❌ Could not load image. Please try again."
#             return redirect(url_for("hirschberg_test"))

#         # Perform Hirschberg test analysis
#         processed_image, text_content, text_filename = analyze_hirschberg(image, HirschbergResults_Folder, latest_image)

#         return render_template(
#             "Hirschberg_Results.html",
#             status="success",
#             message="✅ Hirschberg test processed successfully.",
#             processed_image=processed_image,
#             text_file=text_filename
#         )

#     except Exception as e:
#         session["error_message"] = f"❌ Error: {str(e)}"
#         return redirect(url_for("hirschberg_test"))
def HirschbergShowResult(userName=None, personDetails=None, connected_device=None):
    try:
        # Get the latest image
        images = sorted(
            [f for f in os.listdir(HIRSCHBERG_FOLDER) if f.endswith((".jpg", ".png"))],
            key=lambda f: os.path.getmtime(os.path.join(HIRSCHBERG_FOLDER, f)),
            reverse=True
        )

        if not images:
            flash("❌ No images found. Please capture an image first.", "error")  # ✅ Use flash instead of session
            return redirect(url_for("hirschberg_test"))

        latest_image = images[0]
        image_path = os.path.join(HIRSCHBERG_FOLDER, latest_image)

        # Check eye status
        eye_status = check_eye_status(image_path)
        print(f"🔍 Eye status: {eye_status}")
        if "⚠️" in eye_status:
            flash(eye_status, "error")  # ✅ Use flash
            return redirect(url_for("hirschberg_test"))

        # Load image
        image = cv2.imread(image_path)
        image=cv2.flip(image,1)
        if image is None:
            flash("❌ Could not load image. Please try again.", "error")  # ✅ Use flash
            return redirect(url_for("hirschberg_test"))

        # Perform Hirschberg test analysis
        processed_image, text_content, text_filename = analyze_hirschberg(image, HirschbergResults_Folder, latest_image)
        #crop_eyes_from_image(processed_image)

        return render_template(
            "Hirschberg_Results.html",
            status="success",
            message="✅ Hirschberg test processed successfully.",
            processed_image=processed_image,
            text_file=text_filename,
            userName=userName,
            personDetails=personDetails,
            connected=connected_device
        )

    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")  # ✅ Use flash
        return redirect(url_for("hirschberg_test"))