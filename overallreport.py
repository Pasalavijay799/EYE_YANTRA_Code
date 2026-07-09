import os
import glob
import json
from fpdf import FPDF
from datetime import datetime
import re
import cv2
import _report_appendix

def safe_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

RESULTS_PATHS = {
    "preliminary": os.path.abspath("Preliminary_Results"),
    "hirschberg": os.path.abspath("Hirschberg_Results"),
    "gaze": os.path.abspath("9GazeResults")
}

OUTPUT_PDF_PATH = os.path.abspath("Overall_Report.pdf")

def get_latest_file(folder, pattern):
    files = glob.glob(os.path.join(folder, pattern))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def find_latest_person_data(userName=None):
    # If userName is specified, prioritize files matching that userName.
    # Otherwise, fallback to the latest modified file.
    def get_latest_match(folder, pattern, user_prefix=None):
        if user_prefix:
            files = glob.glob(os.path.join(folder, f"*{user_prefix}*{pattern}"))
            if files:
                return max(files, key=os.path.getctime)
        files = glob.glob(os.path.join(folder, f"*{pattern}"))
        if not files:
            return None
        return max(files, key=os.path.getctime)

    user_prefix = userName if userName else None

    # Preliminary
    latest_prelim = get_latest_match(RESULTS_PATHS["preliminary"], ".jpg", user_prefix)
    latest_prelim_txt = get_latest_match(RESULTS_PATHS["preliminary"], ".txt", user_prefix)

    # Hirschberg
    latest_hirschberg = get_latest_match(RESULTS_PATHS["hirschberg"], ".jpg", user_prefix)
    latest_hirschberg_txt = get_latest_match(RESULTS_PATHS["hirschberg"], ".txt", user_prefix)

    # 9Gaze (look inside the subdirectories)
    gaze_dirs = glob.glob(os.path.join(RESULTS_PATHS["gaze"], "*_Areal"))
    if user_prefix:
        matching_dirs = [d for d in gaze_dirs if user_prefix in os.path.basename(d)]
        latest_gaze_folder = max(matching_dirs, key=os.path.getctime, default=None) if matching_dirs else None
    else:
        latest_gaze_folder = max(gaze_dirs, key=os.path.getctime, default=None) if gaze_dirs else None

    latest_gaze_img = os.path.join(latest_gaze_folder, "combined_9gaze.jpg") if latest_gaze_folder else None
    latest_gaze_txt = os.path.join(latest_gaze_folder, "areal_ratios.txt") if latest_gaze_folder else None

    grades_summary_file = None
    if latest_gaze_folder:
        matching_files = glob.glob(os.path.join(latest_gaze_folder, "*grades_summary.txt"))
        grades_summary_file = matching_files[0] if matching_files else None

    return {
        "preliminary": (latest_prelim, latest_prelim_txt),
        "hirschberg": (latest_hirschberg, latest_hirschberg_txt),
        "gaze": (latest_gaze_img, latest_gaze_txt),
        "grade_summary": (None, grades_summary_file)
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
            up_dev.append(abs(get_dev(b['distances'])))
        elif b['image'] in down_imgs:
            down_dev.append(abs(get_dev(b['distances'])))
        elif b['image'] == primary_img:
            primary_dev = abs(get_dev(b['distances']))

    avg_up = sum(up_dev)/len(up_dev) if up_dev else 0
    avg_down = sum(down_dev)/len(down_dev) if down_dev else 0
    diff = avg_up - avg_down

    if diff >= 5 or diff <= -5:
        if avg_up > avg_down:
            result = "V-pattern detected"
        elif avg_up < avg_down:
            result = "A-pattern detected" 
        elif avg_up > primary_dev and avg_down < primary_dev:
            result = "X-pattern detected"
        elif avg_up > primary_dev and primary_dev >= avg_down:
            result = "Y-pattern detected"
        elif avg_down > primary_dev and primary_dev >= avg_up:       
            result = "Reverse Y-pattern detected"
        else:
            result = "No significant pattern"
    else: 
        result = "No significant pattern"
    return avg_up, avg_down, primary_dev, diff, result

def generate_pdf_report(personDetails):
    raw_user_name = f"{personDetails.get('userName', '')}_{personDetails.get('id', '')}_{personDetails.get('dob', '')}"
    userName = re.sub(r'[\\/*?:"<>|]', '_', raw_user_name)
    person_data = find_latest_person_data(userName=userName)

    # Load admin configuration with defaults
    admin_config = {
        "clinic_name": "Comprehensive Ocular Alignment Report",
        "doctor_name": "Dr. A. Narayana, MBBS, DOMS",
        "doctor_title": "Reviewing Ophthalmologist",
        "tech_name": "T. Kumar",
        "tech_title": "Examining Technician",
        "device_name": "EyeYantra v1.0",
        "contact_email": "reports@eyeyantra.health",
        "contact_phone": "+91 00000 00000"
    }
    if os.path.exists("admin_config.json"):
        try:
            with open("admin_config.json", "r", encoding="utf-8") as f:
                user_config = json.load(f)
                admin_config.update(user_config)
        except Exception as e:
            print(f"⚠️ Error loading admin_config.json: {e}")

    # 1. Initialize FPDF document (A4 size default: 210mm x 297mm)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False, margin=0)
    pdf.alias_nb_pages()  # {nb} placeholder for total pages

    # Brand Palette - Professional Clinical
    C_NAVY = (15, 23, 42)         # Deep navy primary
    C_TEAL = (30, 82, 152)        # Professional medical blue
    C_DARK = (15, 23, 42)         # Deep navy
    C_MUTED = (100, 116, 139)     # Muted slate

    C_SUCCESS = (22, 130, 100)       # Clinical teal
    C_SUCCESS_BG = (235, 248, 244)   # Teal tint
    C_WARN = (190, 140, 30)          # Professional amber
    C_WARN_BG = (253, 246, 220)      # Amber tint
    C_DANGER = (195, 55, 55)         # Clinical red
    C_DANGER_BG = (253, 240, 240)    # Red tint

    C_LIGHT_BG = (245, 247, 250)     # Light clinical gray
    C_BORDER = (210, 218, 228)       # Border gray

    # Helper function to draw section titles
    def draw_section_header(pdf, number, title, status_text, status_type, y):
        pdf.set_xy(10, y)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*C_NAVY)
        pdf.cell(100, 6, f"{number}  {title}", ln=0)
        
        # Draw status badge (right-aligned, dynamic width)
        badge_w = max(28, pdf.get_string_width(status_text) + 10)
        badge_x = 200 - badge_w
        badge_h = 5
        
        if status_type == "success":
            pdf.set_fill_color(*C_SUCCESS_BG)
            pdf.set_text_color(*C_SUCCESS)
        elif status_type == "warn":
            pdf.set_fill_color(*C_WARN_BG)
            pdf.set_text_color(*C_WARN)
        else:
            pdf.set_fill_color(*C_DANGER_BG)
            pdf.set_text_color(*C_DANGER)
            
        pdf.set_xy(badge_x, y + 0.5)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(badge_w, badge_h, status_text, border=0, ln=0, align="C", fill=True)

    # Shared aspect-ratio-preserving image placement (dedupes the repeated
    # OpenCV-read-and-fit block that used to appear separately for each image).
    def draw_fitted_image(pdf, path, x, y, w, h, border_color=C_NAVY):
        if not path or not os.path.exists(path):
            return
        pdf.set_draw_color(*border_color)
        pdf.rect(x - 0.5, y - 0.5, w + 1, h + 1, style="D")
        try:
            im_cv = cv2.imread(path)
            if im_cv is not None:
                h_orig, w_orig = im_cv.shape[:2]
                aspect = w_orig / h_orig
                target_aspect = w / h
                if aspect > target_aspect:
                    draw_w = w
                    draw_h = w / aspect
                    offset_x = 0
                    offset_y = (h - draw_h) / 2
                else:
                    draw_h = h
                    draw_w = h * aspect
                    offset_y = 0
                    offset_x = (w - draw_w) / 2
                pdf.image(path, x=x + offset_x, y=y + offset_y, w=draw_w, h=draw_h)
            else:
                pdf.image(path, x=x, y=y, w=w, h=h)
        except Exception:
            try:
                pdf.image(path, x=x, y=y, w=w, h=h)
            except Exception:
                pass

    # ---------------- PAGE 1 ----------------
    pdf.add_page()
    
    # Header Banner
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(10, 8, 190, 16, style="F")
    
    # Left colored accent line inside header banner
    pdf.set_fill_color(*C_TEAL) # sky blue
    pdf.rect(10, 8, 1.5, 16, style="F")
    
    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 8, safe_text(admin_config.get("clinic_name", "Comprehensive Ocular Alignment Report")), ln=0)
    
    # Subtitle
    pdf.set_xy(15, 17)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_TEAL)
    pdf.cell(100, 4, "Strabismus Screening - Preliminary, Hirschberg & 9-Gaze Assessment", ln=0)
    
    # Report Meta (Right side of banner)
    pdf.set_xy(145, 10)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(50, 4, "REPORT ID: EYT-2026-000054", ln=0, align="R")
    pdf.set_xy(145, 14)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.cell(50, 4, f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M %p')}", ln=0, align="R")
    
    # Patient Info Box
    pdf.set_xy(10, 27)
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_draw_color(*C_BORDER)
    pdf.rect(10, 27, 190, 20, style="FD")
    
    # Left colored accent line inside patient info box
    pdf.set_fill_color(*C_TEAL)
    pdf.rect(10, 27, 1.5, 20, style="F")
    
    # Patient details content
    pdf.set_text_color(*C_NAVY)
    
    # Column 1
    pdf.set_xy(14, 29)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(25, 4, "PATIENT NAME", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 4, str(personDetails.get('userName', 'N/A')), ln=0)
    
    # ... (Wait, let's keep all details unmodified)
    pdf.set_xy(14, 33)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(25, 4, "PATIENT ID", ln=0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(40, 4, str(personDetails.get('id', 'N/A')), ln=0)
    
    pdf.set_xy(14, 37)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(25, 4, "DATE OF BIRTH", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 4, str(personDetails.get('dob', 'N/A')), ln=0)
    
    pdf.set_xy(14, 41)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(25, 4, "EXAM DATE", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 4, datetime.now().strftime('%d-%m-%Y'), ln=0)
    
    # Column 2
    pdf.set_xy(100, 29)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 4, "REFERRING PHYSICIAN", ln=0)
    pdf.set_font("Helvetica", "", 9)
    # Use config doctor name (strip DOMS degree if present for shorter space)
    raw_doc = admin_config.get("doctor_name", "Dr. A. Narayana, MBBS, DOMS")
    doc_short = raw_doc.split(", DOMS")[0]
    pdf.cell(45, 4, safe_text(doc_short), ln=0)
    
    pdf.set_xy(100, 33)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 4, "EXAMINING TECH.", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(45, 4, safe_text(admin_config.get("tech_name", "T. Kumar")), ln=0)
    
    pdf.set_xy(100, 37)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 4, "DEVICE", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(45, 4, safe_text(admin_config.get("device_name", "EyeYantra v1.0")), ln=0)
    
    pdf.set_xy(100, 41)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 4, "SESSION", ln=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(45, 4, "#33", ln=0)

    # ---------------- SECTION 1: PRELIMINARY SCREENING ----------------
    prelim_img, prelim_txt = person_data["preliminary"]
    prelim_diagnosis = "No gross misalignment detected at preliminary screening."
    prelim_her = prelim_ver = "N/A"
    prelim_h_squint = prelim_v_squint = "N/A"
    prelim_rt = prelim_lt = "Within normal limits"
    
    if prelim_txt and os.path.exists(prelim_txt):
        with open(prelim_txt, "r") as f:
            content = f.read()
            if "Esotropia" in content:
                prelim_diagnosis = "Horizontal squint (Esotropia) detected."
                prelim_rt = "Review Required"
            elif "Exotropia" in content:
                prelim_diagnosis = "Horizontal squint (Exotropia) detected."
                prelim_lt = "Review Required"
            
            # parse HER/VER
            her_match = re.search(r"HER:\s*([\d\.-]+)", content)
            ver_match = re.search(r"VER:\s*([\d\.-]+)", content)
            if her_match: prelim_her = her_match.group(1)
            if ver_match: prelim_ver = ver_match.group(1)
            # parse squint values
            for _ln in content.split("\n"):
                _ls = _ln.strip()
                if "Esotropia" in _ls or "Exotropia" in _ls:
                    prelim_h_squint = "Yes"
                if "Horizontal Squint" in _ls and prelim_h_squint == "N/A":
                    prelim_h_squint = _ls.split(":")[-1].strip() if ":" in _ls else "N/A"
                elif "Vertical Squint" in _ls:
                    prelim_v_squint = _ls.split(":")[-1].strip() if ":" in _ls else "N/A"

    y_sec1 = 51
    draw_section_header(pdf, "1", "Preliminary Screening", "CAPTURED - CLEAR", "success", y_sec1)
    
    # Left Column (Data & Description)
    pdf.set_xy(10, y_sec1 + 7)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(90, 4, "Basic eye-alignment screening - corneal landmark detection (RT/RR, LT/LR)", ln=1)
    
    # Landmark Table
    table_y = y_sec1 + 13
    pdf.set_draw_color(*C_BORDER)
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    
    # Headers
    pdf.set_xy(10, table_y)
    pdf.cell(20, 6, "LANDMARK", border=1, fill=True)
    pdf.cell(45, 6, "REGION / DESCRIPTION", border=1, fill=True)
    pdf.cell(30, 6, "STATUS", border=1, fill=True, align="C")
    
    # Row 1
    pdf.set_xy(10, table_y + 6)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(20, 6, "RT / RR", border=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(45, 6, "Right eye - temporal / pupil reflex", border=1)
    pdf.set_font("Helvetica", "B", 8)
    if prelim_rt != "Within normal limits":
        pdf.set_text_color(*C_DANGER)
    else:
        pdf.set_text_color(*C_SUCCESS)
    pdf.cell(30, 6, prelim_rt, border=1, align="C")
    
    # Row 2
    pdf.set_xy(10, table_y + 12)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(20, 6, "LT / LR", border=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(45, 6, "Left eye - temporal / pupil reflex", border=1)
    pdf.set_font("Helvetica", "B", 8)
    if prelim_lt != "Within normal limits":
        pdf.set_text_color(*C_DANGER)
    else:
        pdf.set_text_color(*C_SUCCESS)
    pdf.cell(30, 6, prelim_lt, border=1, align="C")
    
    # Section 1 Diagnosis Box
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_xy(10, table_y + 20)
    pdf.rect(10, table_y + 20, 95, 18, style="D")
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(95, 4, "Preliminary Clinical Impression:", ln=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(11, table_y + 24)
    pdf.multi_cell(93, 3.5, prelim_diagnosis + " Proceed to Hirschberg and 9-Gaze testing for confirmation.", border=0)
    sec1_text_bottom = max(pdf.get_y(), table_y + 20 + 18)

    # Right Column (Preliminary Image)
    prelim_img_bottom = y_sec1 + 7
    if prelim_img and os.path.exists(prelim_img):
        img_x, img_y, img_w, img_h = 112, y_sec1 + 7, 88, 48
        draw_fitted_image(pdf, prelim_img, img_x, img_y, img_w, img_h)
        prelim_img_bottom = img_y + img_h

    sec1_content_bottom = max(sec1_text_bottom, prelim_img_bottom)

    # ---------------- SECTION 2: HIRSCHBERG CORNEAL REFLEX TEST ----------------
    hirsch_img, hirsch_txt = person_data["hirschberg"]
    hirsch_diagnosis = "No gross misalignment detected. Normal corneal light reflex."
    hirsch_l_pos = "Within normal limits"
    hirsch_r_pos = "Within normal limits"
    hirsch_l_dev = "0°"
    hirsch_r_dev = "0°"
    hirsch_status_text = "CAPTURED - CLEAR"
    hirsch_status_type = "success"
    # Detailed Hirschberg values for appendix
    hirsch_lv = hirsch_lh = hirsch_rv = hirsch_rh = "N/A"
    hirsch_left_white = hirsch_right_white = "0.00"
    hirsch_rvd_raw = hirsch_rhd_raw = hirsch_lvd_raw = hirsch_lhd_raw = "N/A"
    hirsch_notes = []

    if hirsch_txt and os.path.exists(hirsch_txt):
        with open(hirsch_txt, "r") as f:
            content = f.read()
            if "Esotropia" in content or "Exotropia" in content or "hypertropia" in content or "hypotropia" in content:
                hirsch_diagnosis = "Corneal reflex displacement noted. Further clinical correlation recommended."
                hirsch_status_text = "REVIEW REQUIRED"
                hirsch_status_type = "warn"
            
            # parse dev angles
            lhd_match = re.search(r"lhd:\s*([\d\.-]+)", content)
            lvd_match = re.search(r"lvd:\s*([\d\.-]+)", content)
            rhd_match = re.search(r"rhd:\s*([\d\.-]+)", content)
            rvd_match = re.search(r"rvd:\s*([\d\.-]+)", content)
            
            def classify_eye_deviation(eye_label, h_mag, v_mag):
                # Sign convention: inward/upward = positive, outward/downward = negative.
                # Reflex position is the inverse of the eye's deviation direction: an
                # esotropic (inward-turned) eye shows the reflex displaced temporally,
                # an exotropic (outward-turned) eye shows it displaced nasally.
                if re.search(rf"{eye_label} Eye likely Esotropia", content):
                    return "Slightly temporal", f"+{h_mag:.1f}°"
                if re.search(rf"{eye_label} Eye likely Exotropia", content):
                    return "Slightly nasal", f"-{h_mag:.1f}°"
                if re.search(rf"{eye_label} Eye likely Hypertropia", content):
                    return "Hypertropia (Upward)", f"+{v_mag:.1f}°"
                if re.search(rf"{eye_label} Eye likely Hypotropia", content):
                    return "Hypotropia (Downward)", f"-{v_mag:.1f}°"
                
                # Check for measured reflex displacement direction (temporal vs nasal)
                dir_match = re.search(rf"{eye_label} Reflex Direction:\s*(\w+)", content)
                if dir_match:
                    reflex_dir = dir_match.group(1).lower()
                    if reflex_dir == "temporal":
                        return "Slightly temporal", f"+{h_mag:.1f}°"
                    elif reflex_dir == "nasal":
                        return "Slightly nasal", f"-{h_mag:.1f}°"
                
                if h_mag > 0.5:
                    return "Slightly nasal", f"-{h_mag:.1f}°"
                return "Within normal limits", "0°"

            lhd_val = float(lhd_match.group(1)) if lhd_match else 0.0
            lvd_val = float(lvd_match.group(1)) if lvd_match else 0.0
            rhd_val = float(rhd_match.group(1)) if rhd_match else 0.0
            rvd_val = float(rvd_match.group(1)) if rvd_match else 0.0

            hirsch_l_pos, hirsch_l_dev = classify_eye_deviation("Left", lhd_val, lvd_val)
            hirsch_r_pos, hirsch_r_dev = classify_eye_deviation("Right", rhd_val, rvd_val)
            # Parse detailed measurements for appendix
            for _hl in content.split("\n"):
                _hs = _hl.strip()
                _hsl = _hs.lower()
                if _hsl.startswith("lv:"):
                    hirsch_lv = _hs.split(":", 1)[-1].strip()
                elif _hsl.startswith("lh:"):
                    hirsch_lh = _hs.split(":", 1)[-1].strip()
                elif _hsl.startswith("rv:"):
                    hirsch_rv = _hs.split(":", 1)[-1].strip()
                elif _hsl.startswith("rh:") and not _hsl.startswith("rhd:"):
                    hirsch_rh = _hs.split(":", 1)[-1].strip()
                elif "left iris white spot" in _hsl:
                    hirsch_left_white = _hs.split(":")[-1].strip()
                elif "right iris white spot" in _hsl:
                    hirsch_right_white = _hs.split(":")[-1].strip()
                elif _hsl.startswith("rvd:"):
                    hirsch_rvd_raw = _hs.split(":", 1)[-1].strip() or "N/A"
                elif _hsl.startswith("rhd:"):
                    hirsch_rhd_raw = _hs.split(":", 1)[-1].strip() or "N/A"
                elif _hsl.startswith("lvd:"):
                    hirsch_lvd_raw = _hs.split(":", 1)[-1].strip() or "N/A"
                elif _hsl.startswith("lhd:"):
                    hirsch_lhd_raw = _hs.split(":", 1)[-1].strip() or "N/A"
                elif _hs and not any(_hsl.startswith(p) for p in ["lv:","lh:","rv:","rh:","lhd:","rhd:","lvd:","rvd:"]) and "iris white" not in _hsl:
                    if any(kw in _hsl for kw in ["hirschberg","report","image path","reflex","detected"]):
                        hirsch_notes.append(_hs)

    y_sec2 = max(120, sec1_content_bottom + 6, y_sec1 + 55 + 6)
    draw_section_header(pdf, "2", "Hirschberg Corneal Reflex Test", hirsch_status_text, hirsch_status_type, y_sec2)
    
    # Left Column (Description)
    pdf.set_xy(10, y_sec2 + 7)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(90, 4, "Corneal light-reflex position relative to pupil centre, both eyes", ln=1)
    
    # Reflex Table
    table_y2 = y_sec2 + 13
    pdf.set_draw_color(*C_BORDER)
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    
    # Headers
    pdf.set_xy(10, table_y2)
    pdf.cell(15, 6, "EYE", border=1, fill=True)
    pdf.cell(45, 6, "REFLEX POSITION", border=1, fill=True)
    pdf.cell(35, 6, "ESTIMATED DEVIATION", border=1, fill=True, align="C")
    
    # Row 1
    pdf.set_xy(10, table_y2 + 6)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(15, 6, "Left", border=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(45, 6, hirsch_l_pos, border=1)
    pdf.set_font("Helvetica", "B", 8)
    if hirsch_l_dev != "0°":
        pdf.set_text_color(*C_DANGER)
    else:
        pdf.set_text_color(*C_SUCCESS)
    pdf.cell(35, 6, hirsch_l_dev, border=1, align="C")
    
    # Row 2
    pdf.set_xy(10, table_y2 + 12)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(15, 6, "Right", border=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(45, 6, hirsch_r_pos, border=1)
    pdf.set_font("Helvetica", "B", 8)
    if hirsch_r_dev != "0°":
        pdf.set_text_color(*C_DANGER)
    else:
        pdf.set_text_color(*C_SUCCESS)
    pdf.cell(35, 6, hirsch_r_dev, border=1, align="C")
    
    # Section 2 Diagnosis Box
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_xy(10, table_y2 + 20)
    pdf.rect(10, table_y2 + 20, 95, 18, style="D")
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(95, 4, "Reflex Localization Clinical Impression:", ln=1)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(11, table_y2 + 24)
    pdf.multi_cell(93, 3.5, hirsch_diagnosis, border=0)
    sec2_text_bottom = max(pdf.get_y(), table_y2 + 20 + 18)

    # Right Column (Hirschberg Image)
    hirsch_img_bottom = y_sec2 + 7
    if hirsch_img and os.path.exists(hirsch_img):
        img_x, img_y, img_w, img_h = 112, y_sec2 + 7, 88, 48
        draw_fitted_image(pdf, hirsch_img, img_x, img_y, img_w, img_h)
        hirsch_img_bottom = img_y + img_h

    sec2_content_bottom = max(sec2_text_bottom, hirsch_img_bottom)

    # ---------------- SECTION 3: NINE-POSITION GAZE TEST ----------------
    # Rendered here (still on Page 1) whenever there's room, instead of always
    # forcing a page break — Page 1 previously left ~90-100mm of blank space
    # below Section 2 (nothing was drawn between it and the y=275 footer).
    SEC3_EST_HEIGHT = 72  # header + description + table/image block
    PAGE1_SAFE_BOTTOM = 268  # leave room for the y=275 footer
    y_sec3_p1 = max(sec2_content_bottom + 6, 178)
    section3_on_page1 = (y_sec3_p1 + SEC3_EST_HEIGHT) <= PAGE1_SAFE_BOTTOM

    if not section3_on_page1:
        # Not enough room this time (long diagnosis/notes pushed content down) -
        # fall back to the original layout: close out Page 1 and start Section 3
        # fresh on Page 2.
        pdf.set_xy(10, 275)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_NAVY)
        pdf.cell(50, 4, "EyeYantra Diagnostics", ln=0)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(90, 4, "SMA Laboratory, IIT Tirupati, Yerpedu - 517619, A.P., India", ln=0, align="C")
        pdf.cell(50, 4, "Page 1 of {nb}", ln=0, align="R")

        pdf.add_page()
        pdf.set_fill_color(*C_NAVY)
        pdf.rect(10, 8, 190, 8, style="F")
        pdf.set_xy(15, 10)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 4, "EyeYantra Automated Ocular Alignment Report", ln=0)
        pdf.set_xy(145, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(50, 4, f"Patient: {personDetails.get('userName', 'N/A')} ({personDetails.get('id', 'N/A')})", ln=0, align="R")
        y_sec3 = 20
    else:
        y_sec3 = y_sec3_p1
    gaze_img, gaze_txt = person_data["gaze"]
    grade_txt = person_data["grade_summary"][1]
    
    # Parse grades
    gaze_table_rows = []
    gaze_directions = {
        "gaze_1.jpg": "Up-Left", "gaze_2.jpg": "Up", "gaze_3.jpg": "Up-Right",
        "gaze_4.jpg": "Left", "gaze_5.jpg": "Primary", "gaze_6.jpg": "Right",
        "gaze_7.jpg": "Down-Left", "gaze_8.jpg": "Down", "gaze_9.jpg": "Down-Right"
    }
    
    blocks = []
    if grade_txt and os.path.exists(grade_txt):
        with open(grade_txt, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        
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
                key, val = [x.strip() for x in line.split(":", 1)]
                if current_section == "grades":
                    current_block["grades"][key] = val
                elif current_section == "distances":
                    current_block["distances"][key] = val
        if current_block["image"]:
            blocks.append(current_block)

    # Parse areal ratios for appendix
    areal_ratios = []
    if gaze_txt and os.path.exists(gaze_txt):
        with open(gaze_txt, "r") as _af:
            for _arl in _af:
                if ":" in _arl:
                    _arp = _arl.strip().split(":")
                    areal_ratios.append((_arp[0].strip(), _arp[1].strip()))

    for i in range(1, 10):
        img_name = f"gaze_{i}.jpg"
        dir_label = gaze_directions[img_name]
        
        # search in parsed blocks
        block = next((b for b in blocks if b["image"] == img_name), None)
        rl = rm = ll = lm = "-"
        if block and block["grades"]:
            rl = block["grades"].get("R_Lateral", "-")
            rm = block["grades"].get("R_Medial", "-")
            ll = block["grades"].get("L_Lateral", "-")
            lm = block["grades"].get("L_Medial", "-")
            
        gaze_table_rows.append((str(i), dir_label, rl, rm, ll, lm))

    draw_section_header(pdf, "3", "Nine-Position Gaze Test", "DEVIATION NOTED", "warn", y_sec3)
    
    # Left Column (Description & Table)
    pdf.set_xy(10, y_sec3 + 7)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(90, 4, "Ocular rotation assessed across all nine cardinal gaze positions", ln=1)
    
    table_y3 = y_sec3 + 12
    pdf.set_draw_color(*C_BORDER)
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*C_NAVY)
    
    # Table Header
    pdf.set_xy(10, table_y3)
    pdf.cell(8, 5, "POS.", border=1, fill=True, align="C")
    pdf.cell(20, 5, "DIRECTION", border=1, fill=True)
    pdf.cell(16, 5, "R_LATERAL", border=1, fill=True, align="C")
    pdf.cell(16, 5, "R_MEDIAL", border=1, fill=True, align="C")
    pdf.cell(16, 5, "L_LATERAL", border=1, fill=True, align="C")
    pdf.cell(16, 5, "L_MEDIAL", border=1, fill=True, align="C")
    
    # Rows
    pdf.set_font("Helvetica", "", 7.5)
    for idx, row in enumerate(gaze_table_rows):
        pdf.set_xy(10, table_y3 + 5 + (idx * 4.6))
        pdf.cell(8, 4.6, row[0], border=1, align="C")
        pdf.cell(20, 4.6, row[1], border=1)
        
        # Style deviations colored red/green
        for j in range(2, 6):
            val = row[j]
            if val != "-" and val != "0" and val != "":
                pdf.set_text_color(*C_DANGER)
                pdf.set_font("Helvetica", "B", 7.5)
            else:
                pdf.set_text_color(*C_NAVY)
                pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(16, 4.6, val, border=1, align="C")

    # Track gaze table bottom for dynamic Section 4 positioning
    gaze_table_bottom = table_y3 + 5 + len(gaze_table_rows) * 4.6
    gaze_img_bottom = y_sec3 + 59  # default if no gaze image

    # Right Column (Composite Gaze Image)
    if gaze_img and os.path.exists(gaze_img):
        img_x, img_y, img_w, img_h = 112, y_sec3 + 7, 88, 52
        gaze_img_bottom = img_y + img_h
        draw_fitted_image(pdf, gaze_img, img_x, img_y, img_w, img_h)

    sec3_content_bottom = max(gaze_table_bottom, gaze_img_bottom)

    if section3_on_page1:
        # Close out Page 1 (Sections 1-3 all fit) and start Page 2 fresh with Section 4.
        footer1_y = max(275, sec3_content_bottom + 6)
        pdf.set_xy(10, footer1_y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_NAVY)
        pdf.cell(50, 4, "EyeYantra Diagnostics", ln=0)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(90, 4, "SMA Laboratory, IIT Tirupati, Yerpedu - 517619, A.P., India", ln=0, align="C")
        pdf.cell(50, 4, "Page 1 of {nb}", ln=0, align="R")

        pdf.add_page()
        pdf.set_fill_color(*C_NAVY)
        pdf.rect(10, 8, 190, 8, style="F")
        pdf.set_xy(15, 10)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 4, "EyeYantra Automated Ocular Alignment Report", ln=0)
        pdf.set_xy(145, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(50, 4, f"Patient: {personDetails.get('userName', 'N/A')} ({personDetails.get('id', 'N/A')})", ln=0, align="R")

    # ---------------- SECTION 4: STRABISMUS PATTERN ANALYSIS ----------------
    pattern_status = "PENDING"
    pattern_status_type = "warn"
    avg_up = avg_down = primary_dev = diff = 0
    pattern_result = "No significant pattern"
    
    if blocks:
        avg_up, avg_down, primary_dev, diff, pattern_result = calculate_av_pattern(blocks)
        if "detected" in pattern_result.lower():
            pattern_status = pattern_result.upper()
            pattern_status_type = "danger"

    if section3_on_page1:
        # Section 3 is on the previous page now - Section 4 starts fresh at the top of Page 2.
        y_sec4 = 20
    else:
        y_sec4 = max(92, gaze_table_bottom + 5, gaze_img_bottom + 5)
    draw_section_header(pdf, "4", "Strabismus Pattern Analysis", pattern_status, pattern_status_type, y_sec4)
    
    # Left Column (Calculated values block)
    pdf.set_xy(10, y_sec4 + 7)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(90, 4, "Horizontal deviation compared across upgaze and downgaze positions", ln=1)
    
    # Render deviation graph locally (drawn as vector graphics natively in FPDF below)
    pass
    
    # Pattern metrics box (taller when Section 4 leads the page, to avoid a
    # sparse-looking Page 2 now that Section 3 has moved to Page 1)
    box_y = y_sec4 + 13
    box_h = 32 if not section3_on_page1 else 48
    row_gap = (box_h - 9) / 3  # evenly space the 4 metric rows inside the box
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_draw_color(*C_BORDER)
    pdf.rect(10, box_y, 95, box_h, style="FD")

    pdf.set_text_color(*C_NAVY)

    metrics = [
        (avg_up, "AVG. UPGAZE DEVIATION"),
        (avg_down, "AVG. DOWNGAZE DEVIATION"),
        (primary_dev, "PRIMARY GAZE DEVIATION"),
        (diff, "UP-DOWN DIFFERENCE"),
    ]
    for i, (val, label) in enumerate(metrics):
        pdf.set_xy(12, box_y + 2 + i * row_gap)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_NAVY)
        pdf.cell(15, 5, f"{val:.2f}", ln=0)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(60, 5, label, ln=1)

    # Description below metrics
    pdf.set_xy(10, box_y + box_h + 2)
    pdf.set_text_color(*C_NAVY)
    pdf.set_font("Helvetica", "", 8)
    if "v-pattern" in pattern_result.lower():
        desc_text = "Deviation increases in upgaze relative to downgaze beyond the primary-gaze baseline, consistent with a V-pattern horizontal deviation. Clinical correlation advised."
    elif "a-pattern" in pattern_result.lower():
        desc_text = "Deviation increases in downgaze relative to upgaze, consistent with an A-pattern horizontal deviation. Clinical correlation advised."
    else:
        desc_text = "No significant horizontal pattern deviation detected across vertical gaze shifts."
    pdf.multi_cell(95, 3.5, desc_text, border=0)
    sec4_text_bottom = pdf.get_y()

    # Right Column (Deviation Graph - drawn natively with vector elements)
    chart_x = 115
    chart_y = y_sec4 + 13
    chart_w = 85
    chart_h = box_h
    
    # Background Box for Chart
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.set_draw_color(*C_BORDER)
    pdf.rect(chart_x, chart_y, chart_w, chart_h, style="FD")
    
    # Left colored accent line inside chart box
    pdf.set_fill_color(*C_TEAL)
    pdf.rect(chart_x, chart_y, 1.5, chart_h, style="F")
    
    # Chart Title
    pdf.set_xy(chart_x + 3, chart_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(chart_w - 6, 4, "Horizontal Deviation Across Gazes", ln=1, align="L")
    
    # Draw Axis line
    axis_y = chart_y + chart_h - 6
    pdf.set_draw_color(148, 163, 184) # Slate-400
    pdf.line(chart_x + 8, axis_y, chart_x + chart_w - 8, axis_y)
    
    # Values and Heights
    max_val = max(avg_up, primary_dev, avg_down)
    if max_val <= 0:
        max_val = 10.0
    scale = (chart_h - 15) / max_val
    
    bar_width = 12
    # X offsets for three bars
    bar_positions = [
        (chart_x + 12, "Upgaze", avg_up, (14, 165, 233)),
        (chart_x + 36, "Primary", primary_dev, (16, 185, 129)),
        (chart_x + 60, "Downgaze", avg_down, (245, 158, 11))
    ]
    
    for bx, label, val, color in bar_positions:
        h = val * scale
        # Draw bar rectangle
        pdf.set_fill_color(*color)
        pdf.rect(bx, axis_y - h, bar_width, h, style="F")
        
        # Draw value text above the bar
        pdf.set_xy(bx, axis_y - h - 3.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(51, 65, 85) # Slate-700
        pdf.cell(bar_width, 3, f"{val:.1f}", ln=0, align="C")
        
        # Draw label below the axis
        pdf.set_xy(bx - 3, axis_y + 1)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(bar_width + 6, 3, label, ln=0, align="C")

    # ---------------- SECTION 5: CLINICAL IMPRESSION & SIGNATURES ----------------
    chart_bottom = chart_y + chart_h
    box5_h = 58
    # When Section 3 has moved to Page 1, Section 4 starts higher up, so let
    # Section 5 follow it immediately instead of sitting on the old fixed
    # floor (158) that assumed Section 4 always started around y=92.
    y_sec5 = max(90 if section3_on_page1 else 158, sec4_text_bottom + 10, chart_bottom + 10)
    pdf.set_xy(10, y_sec5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(100, 6, "5  Clinical Impression", ln=1)

    # Outline Border Box
    pdf.set_draw_color(*C_BORDER)
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, y_sec5 + 7, 190, box5_h, style="D")

    pdf.set_xy(14, y_sec5 + 10)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_NAVY)

    impression_txt = (
        f"Automated eye test analysis reports a '{pattern_result}' based on vertical gaze differences. "
        "Corneal light reflex landmark positions and reflex deviations measured on Hirschberg test confirm alignment details. "
        "Findings are within the range typically followed up with comprehensive orthoptic examination. "
        "This report is generated by the EyeYantra automated ocular-alignment analysis system and is intended to support "
        "&mdash; not replace &mdash; clinical evaluation by a qualified ophthalmologist."
    )
    # Replace HTML entity
    impression_txt = impression_txt.replace("&mdash;", "--")
    pdf.multi_cell(182, 4, impression_txt, border=0)

    # Signatures
    sig_y = y_sec5 + 40

    # Tech
    pdf.line(20, sig_y + 14, 80, sig_y + 14)
    pdf.set_xy(20, sig_y + 15)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(60, 4, safe_text(admin_config.get("tech_name", "T. Kumar")), ln=1, align="C")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_MUTED)
    pdf.set_xy(20, sig_y + 19)
    pdf.cell(60, 4, safe_text(admin_config.get("tech_title", "Examining Technician")), ln=0, align="C")

    # Doctor
    pdf.set_text_color(*C_NAVY)
    pdf.line(130, sig_y + 14, 190, sig_y + 14)
    pdf.set_xy(130, sig_y + 15)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(60, 4, safe_text(admin_config.get("doctor_name", "Dr. A. Narayana, MBBS, DOMS")), ln=1, align="C")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_MUTED)
    pdf.set_xy(130, sig_y + 19)
    pdf.cell(60, 4, safe_text(admin_config.get("doctor_title", "Reviewing Ophthalmologist")), ln=0, align="C")

    # Disclaimer Box (dynamically positioned below signatures, capped so it
    # never collides with the footer)
    sig_bottom = sig_y + 23
    disclaimer_y = max(262, sig_bottom + 4)
    pdf.set_xy(10, disclaimer_y)
    pdf.set_fill_color(*C_DANGER_BG)
    pdf.set_draw_color(*C_DANGER)
    pdf.rect(10, disclaimer_y, 190, 10, style="FD")
    pdf.set_xy(12, disclaimer_y + 1.5)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*C_DANGER)
    pdf.cell(15, 4, "WARNING:", ln=0)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(170, 4, "This is an automated screening report. Clinicians must verify the annotated landmarks prior to making clinical decisions.", ln=0)

    # Footer Page 2 (dynamically positioned below disclaimer)
    footer_y = max(275, disclaimer_y + 13)
    pdf.set_xy(10, footer_y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_NAVY)
    pdf.cell(50, 4, "EyeYantra Diagnostics", ln=0)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_MUTED)
    contact_email = admin_config.get("contact_email", "reports@eyeyantra.health")
    contact_phone = admin_config.get("contact_phone", "+91 00000 00000")
    pdf.cell(90, 4, safe_text(f"Reports: {contact_email}  |  Support: {contact_phone}"), ln=0, align="C")
    pdf.cell(50, 4, "Page 2 of {nb}", ln=0, align="R")

    # Render detailed appendix pages (pages 3+)
    _report_appendix.render_appendix(pdf, locals())

    pdf.output(OUTPUT_PDF_PATH)
    return OUTPUT_PDF_PATH, pattern_result