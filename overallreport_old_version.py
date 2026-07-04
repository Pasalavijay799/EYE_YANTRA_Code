import os
import glob
from fpdf import FPDF
from datetime import datetime
import re
import matplotlib.pyplot as plt

def safe_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

RESULTS_PATHS = {
    "preliminary": "Preliminary_Results",
    "hirschberg": "Hirschberg_Results",
    "gaze": "9GazeResults"
}

OUTPUT_PDF_PATH = "Overall_Report.pdf"

def get_latest_file(folder, pattern):
    files = glob.glob(os.path.join(folder, pattern))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def find_latest_person_data():
    latest_prelim = get_latest_file(RESULTS_PATHS["preliminary"], "*.jpg")
    latest_prelim_txt = get_latest_file(RESULTS_PATHS["preliminary"], "*.txt")

    latest_hirschberg = get_latest_file(RESULTS_PATHS["hirschberg"], "*.jpg")
    latest_hirschberg_txt = get_latest_file(RESULTS_PATHS["hirschberg"], "*.txt")

    latest_gaze_folder = max(glob.glob(os.path.join(RESULTS_PATHS["gaze"], "*")), key=os.path.getctime, default=None)
    latest_gaze_img = os.path.join(latest_gaze_folder, "combined_9gaze.jpg") if latest_gaze_folder else None
    latest_gaze_txt = os.path.join(latest_gaze_folder, "areal_ratios.txt") if latest_gaze_folder else None

    grades_summary_file = None
    if latest_gaze_folder:
        matching_files = glob.glob(os.path.join(latest_gaze_folder, "*grades_summary.txt"))
        grades_summary_file = matching_files[0] if matching_files else None
    print(grades_summary_file)

    return {
        "preliminary": (latest_prelim, latest_prelim_txt),
        "hirschberg": (latest_hirschberg, latest_hirschberg_txt),
        "gaze": (latest_gaze_img, latest_gaze_txt),
        "grade_summary":(None,grades_summary_file)
    }


def calculate_av_pattern(blocks):
    up_imgs = ["gaze_1.jpg", "gaze_2.jpg", "gaze_3.jpg"]
    down_imgs = ["gaze_7.jpg", "gaze_8.jpg", "gaze_9.jpg"]
    primary_img = "gaze_5.jpg"

    def get_dev(dist):
        try:
            rlat = float(dist.get("R_Lateral", 0))
            rmed = float(dist.get("R_Medial", 0))
            llat = float(dist.get("L_Lateral", 0))
            lmed = float(dist.get("L_Medial", 0))
            return (rlat - rmed) + (llat - lmed)
        except:
            return 0
    up_dev, down_dev, primary_dev = [], [], 0

    for b in blocks:
        if b['image'] in up_imgs:
            up_dev.append(abs(get_dev(b['distances'])))   # ✔ magnitude
        elif b['image'] in down_imgs:
            down_dev.append(abs(get_dev(b['distances']))) # ✔ magnitude
        elif b['image'] == primary_img:
            primary_dev = abs(get_dev(b['distances']))    # ✔ magnitude

    avg_up = sum(up_dev)/len(up_dev) if up_dev else 0
    avg_down = sum(down_dev)/len(down_dev) if down_dev else 0

    '''up_dev, down_dev, primary_dev = [], [], 0
    for b in blocks:
        if b['image'] in up_imgs:
            up_dev.append(get_dev(b['distances']))
        elif b['image'] in down_imgs:
            down_dev.append(get_dev(b['distances']))
        elif b['image'] == primary_img:
            primary_dev = get_dev(b['distances'])

    avg_up = sum(up_dev)/len(up_dev) if up_dev else 0
    avg_down = sum(down_dev)/len(down_dev) if down_dev else 0'''
    diff = avg_up - avg_down
    # ⭐ Pattern Logic
    '''if avg_up > primary_dev + 10 and avg_down > primary_dev + 10:
        result = "X-pattern detected"

    elif avg_up > primary_dev + 10 and primary_dev > avg_down + 10:
        result = "Y-pattern detected"

    elif avg_down > primary_dev + 10 and primary_dev > avg_up + 10:
        result = "Reverse Y-pattern detected"

    elif diff >= 15:
        result = "V-pattern detected"

    elif diff <= -10:
        result = "A-pattern detected"

    else:
        result = "No significant pattern" ''' 


   # result = "No A or V pattern detected"
    if avg_up > avg_down:
        result = "A-pattern detected"
    elif avg_up < avg_down:
        result = "V-pattern detected" 
    elif avg_up < primary_dev and avg_down < primary_dev:
        result = "X-pattern detected"
    elif avg_up < primary_dev:
        result = "Y-pattern detected"
    elif avg_down < primary_dev:
        result = "Reverse Y-pattern detected"
    else:
         result = "No significant pattern"

    return avg_up, avg_down, primary_dev, diff, result


def generate_pdf_report(personDetails):
    person_data = find_latest_person_data()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    first_page = True
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Define color scheme
    HEADER_COLOR = (41, 128, 185)      # Professional blue
    ACCENT_COLOR = (52, 152, 219)      # Light blue
    TEXT_COLOR = (44, 62, 80)          # Dark gray
    TABLE_HEADER_COLOR = (236, 240, 241) # Light gray
    TABLE_ALT_COLOR = (248, 249, 250)    # Very light gray

    def set_header_style():
        pdf.set_fill_color(*HEADER_COLOR)
        pdf.set_text_color(255, 255, 255)
        
    def set_subheader_style():
        pdf.set_fill_color(*ACCENT_COLOR)
        pdf.set_text_color(255, 255, 255)
        
    def set_normal_text_style():
        pdf.set_text_color(*TEXT_COLOR)
        pdf.set_fill_color(255, 255, 255)
        
    def set_table_header_style():
        pdf.set_fill_color(*TABLE_HEADER_COLOR)
        pdf.set_text_color(*TEXT_COLOR)
        
    def set_table_row_style(alternate=False):
        if alternate:
            pdf.set_fill_color(*TABLE_ALT_COLOR)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*TEXT_COLOR)

    def draw_header_line():
        """Draw a decorative line under headers"""
        pdf.set_draw_color(*ACCENT_COLOR)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(5)

    for test, (image, text_file) in person_data.items():
        if image and text_file:
            pdf.add_page()

            # Add styled datetime header with background - centered
            set_header_style()
            pdf.set_font("Arial", "B", 10)
            pdf.set_xy(70, 8)
            pdf.cell(60, 8, f"Generated: {now_str}", ln=1, align="C", fill=True)
            
            # Reset to normal style
            set_normal_text_style()

            if first_page:
                # Main title with background and border - centered
                pdf.ln(10)
                set_header_style()
                pdf.set_font("Arial", "B", 20)
                pdf.set_x(10)
                pdf.cell(190, 15, "COMPREHENSIVE EYE TEST REPORT", ln=True, align="C", fill=True)
                draw_header_line()
                
                # Personal details section with styled background - centered
                pdf.ln(5)
                set_subheader_style()
                pdf.set_font("Arial", "B", 14)
                pdf.set_x(10)
                pdf.cell(190, 12, "Patient Information", ln=True, align="C", fill=True)
                
                set_normal_text_style()
                pdf.ln(5)
                
                # Personal details in styled boxes - centered
                pdf.set_font("Arial", "B", 12)
                details = [
                    ("Name", personDetails.get('userName', 'N/A')),
                    ("Date of Birth", personDetails.get('dob', 'N/A')),
                    ("Patient ID", personDetails.get('id', 'N/A'))
                ]
                
                # Center the table
                table_width = 190
                start_x = (210 - table_width) / 2
                
                for i, (label, value) in enumerate(details):
                    set_table_row_style(i % 2 == 1)
                    pdf.set_x(start_x)
                    pdf.cell(60, 10, f"{label}:", border=1, fill=True)
                    pdf.cell(130, 10, value, border=1, fill=True)
                    pdf.ln()
                
                pdf.ln(10)
                pdf.add_page()
                first_page = False

            # Test section header with styling - centered
            set_subheader_style()
            pdf.set_font("Arial", "B", 16)
            test_title = f"{test.replace('_', ' ').title()} Test Results"
            pdf.set_x(10)
            pdf.cell(190, 12, test_title, ln=True, align="C", fill=True)
            draw_header_line()

            # Add image with border - centered
            pdf.set_draw_color(*ACCENT_COLOR)
            pdf.set_line_width(1)
            image_width = 180
            image_x = (210 - image_width) / 2
            pdf.rect(image_x - 1, 49, image_width + 2, 102)  # Border around image
            pdf.image(image, x=image_x, y=50, w=image_width)

            if test == "preliminary":
                pdf.ln(130)
                
                # Styled section header - centered
                set_subheader_style()
                pdf.set_font("Arial", "B", 14)
                pdf.set_x(10)
                pdf.cell(190, 10, "Preliminary Analysis Report", ln=True, align="C", fill=True)
                pdf.ln(8)

                her = ver = h_squint = v_squint = "N/A"

                with open(text_file, "r") as f:
                    for line in f:
                        #print(line)
                        line = line.strip()
                        if "HER" in line:
                            her = line.split(":")[-1].strip()
                        elif "VER" in line:
                            ver = line.split(":")[-1].strip()
                        elif "Horizontal Squint" in line:
                            h_squint = "Yes" if "Yes" in line else "No"
                        elif "Vertical Squint" in line:
                            v_squint = "Yes" if "Yes" in line else "No"

                # Styled table - centered
                col_width = 95
                row_height = 12
                table_width = col_width * 2
                start_x = (210 - table_width) / 2
                
                # Table header
                set_table_header_style()
                pdf.set_font("Arial", "B", 12)
                pdf.set_x(start_x)
                pdf.cell(col_width, row_height, "Parameter", border=1, fill=True)
                pdf.cell(col_width, row_height, "Value", border=1, fill=True)
                pdf.ln()
                
                # Table rows with alternating colors
                rows = [("HER", her), ("VER", ver), ("Horizontal Squint", h_squint), ("Vertical Squint", v_squint)]
                pdf.set_font("Arial", "", 11)
                
                for i, (param, value) in enumerate(rows):
                    set_table_row_style(i % 2 == 1)
                    pdf.set_x(start_x)
                    pdf.cell(col_width, row_height, param, border=1, fill=True)
                    pdf.cell(col_width, row_height, value, border=1, fill=True)
                    pdf.ln()



            elif test == "gaze":
                pdf.ln(120)
                
                # Styled section header - centered
                set_subheader_style()
                pdf.set_font("Arial", "B", 14)
                pdf.set_x(10)
                pdf.cell(190, 10, "9 Gaze Analysis Report", ln=True, align="C", fill=True)
                pdf.ln(8)

                with open(text_file, "r") as f:
                    lines = f.readlines()

                # Table header - centered
                col_width = 95
                table_width = col_width * 2
                start_x = (210 - table_width) / 2
                
                set_table_header_style()
                pdf.set_font("Arial", "B", 12)
                pdf.set_x(start_x)
                pdf.cell(col_width, 12, "Gaze Position", border=1, fill=True)
                pdf.cell(col_width, 12, "Areal Ratio", border=1, fill=True)
                pdf.ln()

                # Table rows - centered
                pdf.set_font("Arial", "", 11)
                row_count = 0
                for line in lines:
                    if ":" in line:
                        gaze_img, ratio = line.strip().split(":")
                        set_table_row_style(row_count % 2 == 1)
                        pdf.set_x(start_x)
                        pdf.cell(col_width, 10, gaze_img.strip(), border=1, fill=True)
                        pdf.cell(col_width, 10, ratio.strip(), border=1, fill=True)
                        pdf.ln()
                        row_count += 1

            

            else:
                pdf.ln(120)
                
                # Styled section header - centered
                set_subheader_style()
                pdf.set_font("Arial", "B", 14)
                pdf.set_x(10)
                pdf.cell(190, 10, "Detailed Analysis Report", ln=True, align="C", fill=True)
                pdf.ln(8)

                with open(text_file, "r") as f:
                    lines = [line.strip() for line in f if line.strip()]

                # Extract specific values by line index and keywords
                lv = lh = rv = rh = ""
                left_white = right_white = ""
                rvd = rhd = lvd = lhd = ""
                remaining_text = []

                for line in lines:
                    lower = line.lower()
                    if lower.startswith("lv:"):
                        lv = line.replace("lv:", "").strip()
                    elif lower.startswith("lh:"):
                        lh = line.replace("lh:", "").strip()
                    elif lower.startswith("rv:"):
                        rv = line.replace("rv:", "").strip()
                    elif lower.startswith("rh:"):
                        rh = line.replace("rh:", "").replace("rh:", "").strip()  # Fixed duplicate key
                    elif "left iris white spot" in lower:
                        left_white = line.split(":")[-1].strip()
                    elif "right iris white spot" in lower:
                        right_white = line.split(":")[-1].strip()
                    elif lower.startswith("rvd:"):
                        rvd = line.replace("rvd:", "").strip()
                    elif lower.startswith("rhd:"):
                        rhd = line.replace("rhd:", "").strip()
                    elif lower.startswith("lvd:"):
                        lvd = line.replace("lvd:", "").strip()
                    elif lower.startswith("lhd:"):
                        lhd = line.replace("lhd:", "").strip()
                    else:
                        remaining_text.append(line)

                # Styled measurement table - centered
                col_width = 90
                row_height = 10
                table_width = col_width * 2
                start_x = (210 - table_width) / 2
                
                # Table header
                set_table_header_style()
                pdf.set_font("Arial", "B", 11)
                pdf.set_x(start_x)
                pdf.cell(col_width, row_height + 2, "Measurement", border=1, fill=True)
                pdf.cell(col_width, row_height + 2, "Value", border=1, fill=True)
                pdf.ln()
                
                # Table data with alternating colors
                measurements = [
                    ("Left Vertical (LV)", lv),
                    ("Left Horizontal (LH)", lh),
                    ("Right Vertical (RV)", rv),
                    ("Right Horizontal (RH)", rh),
                    ("Left Iris White Spot", left_white),
                    ("Right Iris White Spot", right_white),
                    ("Right Vertical Distance (RVD)", rvd),
                    ("Right Horizontal Distance (RHD)", rhd),
                    ("Left Vertical Distance (LVD)", lvd),
                    ("Left Horizontal Distance (LHD)", lhd)
                ]
                
                pdf.set_font("Arial", "", 10)
                for i, (param, value) in enumerate(measurements):
                    set_table_row_style(i % 2 == 1)
                    pdf.set_x(start_x)
                    pdf.cell(col_width, row_height, param, border=1, fill=True)
                    pdf.cell(col_width, row_height, value or "N/A", border=1, fill=True)
                    pdf.ln()

                # Additional notes section - centered
                if remaining_text:
                    pdf.ln(8)
                    set_subheader_style()
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_x(10)
                    pdf.cell(190, 10, "Additional Notes", ln=True, align="C", fill=True)
                    pdf.ln(5)
                    
                    set_normal_text_style()
                    pdf.set_font("Arial", "", 10)
                    notes_width = 180
                    notes_start_x = (210 - notes_width) / 2
                    for i, line in enumerate(remaining_text):
                        set_table_row_style(i % 2 == 1)
                        pdf.set_x(notes_start_x)
                        pdf.cell(notes_width, 8, line, ln=True, fill=True, border=1, align="C")
        
        elif test == "grade_summary" and text_file:
            pdf.add_page()

            # Section header
            set_subheader_style()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(190, 12, "Grade Summary Report", ln=True, align="C", fill=True)
            draw_header_line()
            pdf.ln(3)

            # Parse the grades_summary.txt
            with open(text_file, "r") as f:
                lines = [line.strip() for line in f if line.strip()]

            blocks = []
            current_block = {"image": "", "grades": {}, "distances": {}}
            current_section = None

            for line in lines:
                if line.startswith("Image:"):
                    if current_block["image"]:
                        blocks.append(current_block)
                        current_block = {"image": "", "grades": {}, "distances": {}}
                    current_block["image"] = line.split("Image:")[-1].strip()

                elif line.startswith("Grades:"):
                    current_section = "grades"
                elif line.startswith("Distances:"):
                    current_section = "distances"
                elif ":" in line:
                    key, value = [x.strip() for x in line.split(":", 1)]
                    if current_section == "grades":
                        current_block["grades"][key] = value
                    elif current_section == "distances":
                        current_block["distances"][key] = value

            # Append last block
            if current_block["image"]:
                blocks.append(current_block)

            # Render each block
            for block in blocks:
                # Subheader for image
                set_table_header_style()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"Image: {block['image']}", ln=True, fill=True)

                # Grades table
                if block["grades"]:
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(0, 8, "Grades", ln=True)
                    pdf.set_font("Arial", "", 10)

                    for i, (k, v) in enumerate(block["grades"].items()):
                        set_table_row_style(i % 2 == 1)
                        pdf.cell(95, 8, k, border=1, fill=True)
                        pdf.cell(95, 8, v, border=1, ln=True, fill=True)
                else:
                    pdf.set_font("Arial", "I", 10)
                    pdf.cell(0, 8, "No grade data available", ln=True)

                pdf.ln(2)

                # Distances table
                if block["distances"]:
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(0, 8, "Distances", ln=True)
                    pdf.set_font("Arial", "", 10)

                    for i, (k, v) in enumerate(block["distances"].items()):
                        set_table_row_style(i % 2 == 1)
                        pdf.cell(95, 8, k, border=1, fill=True)
                        pdf.cell(95, 8, v, border=1, ln=True, fill=True)

                pdf.ln(10)

            # Your existing generate_pdf_report function remains unchanged until the grade_summary section
            # Append this code inside the 'elif test == "grade_summary" and text_file:' block after the distances table rendering:

            # Add A/V Pattern Section
            pdf.add_page()
            avg_up, avg_down, primary_dev, diff, result = calculate_av_pattern(blocks)
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(190, 10, "Strabismus Pattern Analysis", ln=True, align="C", fill=True)
            pdf.set_draw_color(52, 152, 219)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(8)

            pdf.set_text_color(44, 62, 80)
            pdf.set_font("Arial", "", 11)

            calculation_description = (
                "To determine pattern strabismus, we compare horizontal deviations across gaze directions:\n"
                "Deviation is calculated for each gaze as:\n"
                "(Right Lateral - Right Medial) + (Left Lateral - Left Medial)\n\n"
                "We average the deviations from:\n"
                "- Upgaze: gaze_1.jpg, gaze_2.jpg, gaze_3.jpg\n"
                "- Downgaze: gaze_7.jpg, gaze_8.jpg, gaze_9.jpg\n"
                "- Primary Gaze: gaze_5.jpg\n\n"
                "The difference between Upgaze and Downgaze helps detect patterns:\n"
            "if avg_up > avg_down:\n"
                    "result = A-pattern detected\n"
                "avg_up < avg_down:\n"
                    "result = V-pattern detected\n" 
                "avg_up < primary_dev and avg_down < primary_dev:\n"
                    "result = X-pattern detected\n"
                "avg_up < primary_dev:\n"
                    "result = Y-pattern detected\n"
                "avg_down < primary_dev:\n"
                    "result = Reverse Y-pattern detected"
            "else:  result = No significant pattern\n"
               
               
            )

            pdf.multi_cell(0, 8, calculation_description, border=1, align="L")
            pdf.ln(2)
            pdf.multi_cell(0, 8, f"Calculated horizontal deviation values:\n\n"
                            f"Average Upgaze Deviation: {avg_up:.2f}\n"
                            f"Average Downgaze Deviation: {avg_down:.2f}\n"
                            f"Primary Gaze Deviation: {primary_dev:.2f}\n"
                           # f"Deviation Difference (Up - Down): {diff:.2f}\n\n"
                            f"Pattern Result: {result}", border=1, align="L")
            
            
            
            avg_up, avg_down, primary_dev, diff, result = calculate_av_pattern(blocks)
            # Retrieve raw values again for display
            up_imgs = ["gaze_1.jpg", "gaze_2.jpg", "gaze_3.jpg"]
            down_imgs = ["gaze_7.jpg", "gaze_8.jpg", "gaze_9.jpg"]

            def get_dev(dist):
                try:
                    rlat = float(dist.get("R_Lateral", 0))
                    rmed = float(dist.get("R_Medial", 0))
                    llat = float(dist.get("L_Lateral", 0))
                    lmed = float(dist.get("L_Medial", 0))
                    return (rlat - rmed) + (llat - lmed)
                except:
                    return 0

            up_dev = [get_dev(b["distances"]) for b in blocks if b["image"] in up_imgs]
            down_dev = [get_dev(b["distances"]) for b in blocks if b["image"] in down_imgs]

            pdf.add_page()
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(190, 10, "Strabismus Pattern Analysis", ln=True, align="C", fill=True)
            pdf.set_draw_color(52, 152, 219)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(8)

            pdf.set_text_color(44, 62, 80)
            pdf.set_font("Arial", "", 11)

            up_values_str = "    ".join([f"{val:.2f}" for val in up_dev])
            down_values_str = "    ".join([f"{val:.2f}" for val in down_dev])

            calculation_description = (
                "To determine Strabismuspattern strabismus, we compare horizontal deviations across gaze directions:\n"
                "Deviation is calculated for each gaze as:\n"
                "(Right Lateral - Right Medial) + (Left Lateral - Left Medial)\n\n"
                "We average the deviations from:\n"
                "- Upgaze (gaze_1.jpg, gaze_2.jpg, gaze_3.jpg):\n"
                f"  Values: {up_values_str}\n"
                f"  Average: {avg_up:.2f}\n\n"
                "- Downgaze (gaze_7.jpg, gaze_8.jpg, gaze_9.jpg):\n"
                f"  Values: {down_values_str}\n"
                f"  Average: {avg_down:.2f}\n\n"
                f"- Primary Gaze (gaze_5.jpg):\n  Value: {primary_dev:.2f}\n\n"
                "The difference between Upgaze and Downgaze helps detect patterns:\n"
                "- If Up > Down : A-pattern\n"
                "- If Up <Down  : V-pattern\n"
                "- If both Upgaze and Downgaze deviations are significantly greater than Primary gaze is X-pattern \n"
                "- If Upgaze deviation > Primary > Downgaze is Y-pattern\n"
                "- If Downgaze deviation > Primary > Upgaze is Reverse Y-pattern\n"
                "- Else: No pattern detected\n"
               # f"\nCalculated Difference (Up - Down): {diff:.2f}\n"
                f"\nFinal Pattern Result: {result}"
            )

            pdf.multi_cell(0, 8, calculation_description, border=1, align="L")



            

            # Create and save graph for deviation visualization
            plt.figure(figsize=(5,3))
            gazes = ["Upgaze", "Primary", "Downgaze"]
            values = [avg_up, primary_dev, avg_down]
            plt.bar(gazes, values, color=['#3498db', '#2ecc71', '#e74c3c'])
            plt.axhline(0, color='black', linewidth=0.8)
            plt.title("Horizontal Deviation Across Gazes")
            plt.ylabel("Deviation Value")
            graph_path = "deviation_chart.png"
            plt.tight_layout()
            plt.savefig(graph_path)
            plt.close()

            # Insert graph into PDF
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 10, "Deviation Visualization", ln=True, align="C", fill=True)
            pdf.ln(8)
            pdf.set_text_color(44, 62, 80)
            pdf.image(graph_path, x=30, w=150)

            # Optionally delete the image after saving PDF
            os.remove(graph_path)


    # Add footer to last page - centered
    pdf.ln(10)
    set_header_style()
    pdf.set_font("Arial", "I", 10)
    pdf.set_x(10)
    pdf.cell(190, 8, "End of Report - Generated by Eye Test Analysis System", ln=True, align="C", fill=True)

    pdf.output(OUTPUT_PDF_PATH)
    return OUTPUT_PDF_PATH