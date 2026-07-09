"""
EyeYantra Report - Detailed Appendix Pages
Renders Pages 3+ with detailed measurements matching the old report format.
"""
import os
import cv2


def safe_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')


def render_appendix(pdf, ctx):
    """Render detailed appendix pages using context from generate_pdf_report."""
    pD = ctx.get('personDetails', {})
    ac = ctx.get('admin_config', {})

    CN = ctx.get('C_NAVY', (15, 23, 42))
    CT = ctx.get('C_TEAL', (30, 82, 152))
    CM = ctx.get('C_MUTED', (100, 116, 139))
    CLB = ctx.get('C_LIGHT_BG', (245, 247, 250))
    CB = ctx.get('C_BORDER', (210, 218, 228))
    CS = ctx.get('C_SUCCESS', (22, 130, 100))
    CSB = ctx.get('C_SUCCESS_BG', (235, 248, 244))
    CW = ctx.get('C_WARN', (190, 140, 30))
    CWB = ctx.get('C_WARN_BG', (253, 246, 220))
    CD = ctx.get('C_DANGER', (195, 55, 55))
    CDB = ctx.get('C_DANGER_BG', (253, 240, 240))

    prelim_img = ctx.get('prelim_img')
    prelim_her = ctx.get('prelim_her', 'N/A')
    prelim_ver = ctx.get('prelim_ver', 'N/A')
    prelim_h_squint = ctx.get('prelim_h_squint', 'N/A')
    prelim_v_squint = ctx.get('prelim_v_squint', 'N/A')

    hirsch_lv = ctx.get('hirsch_lv', 'N/A')
    hirsch_lh = ctx.get('hirsch_lh', 'N/A')
    hirsch_rv = ctx.get('hirsch_rv', 'N/A')
    hirsch_rh = ctx.get('hirsch_rh', 'N/A')
    hirsch_left_white = ctx.get('hirsch_left_white', '0.00')
    hirsch_right_white = ctx.get('hirsch_right_white', '0.00')
    hirsch_rvd_raw = ctx.get('hirsch_rvd_raw', 'N/A')
    hirsch_rhd_raw = ctx.get('hirsch_rhd_raw', 'N/A')
    hirsch_lvd_raw = ctx.get('hirsch_lvd_raw', 'N/A')
    hirsch_lhd_raw = ctx.get('hirsch_lhd_raw', 'N/A')
    hirsch_notes = ctx.get('hirsch_notes', [])

    areal_ratios = ctx.get('areal_ratios', [])
    gaze_img = ctx.get('gaze_img')
    blocks = ctx.get('blocks', [])
    gaze_directions = ctx.get('gaze_directions', {})

    avg_up = ctx.get('avg_up', 0)
    avg_down = ctx.get('avg_down', 0)
    primary_dev = ctx.get('primary_dev', 0)
    diff = ctx.get('diff', 0)
    pattern_result = ctx.get('pattern_result', 'No significant pattern')

    # ---- Helpers ----
    def _hdr(title):
        pdf.set_fill_color(*CN)
        pdf.rect(10, 8, 190, 8, style="F")
        pdf.set_fill_color(*CT)
        pdf.rect(10, 8, 1.5, 8, style="F")
        pdf.set_xy(15, 10)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 4, safe_text(title), ln=0)
        pdf.set_xy(145, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(50, 4, f"Patient: {pD.get('userName','N/A')} ({pD.get('id','N/A')})", ln=0, align="R")

    def _ftr():
        pdf.set_xy(10, 282)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*CN)
        pdf.cell(50, 4, "EyeYantra Diagnostics", ln=0)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*CM)
        ce = ac.get("contact_email", "reports@eyeyantra.health")
        cp = ac.get("contact_phone", "+91 00000 00000")
        pdf.cell(90, 4, safe_text(f"Reports: {ce}  |  Support: {cp}"), ln=0, align="C")
        pdf.cell(50, 4, f"Page {pdf.page_no()} of {{nb}}", ln=0, align="R")

    def _sec(num, title, badge, btype, y):
        pdf.set_xy(10, y)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*CN)
        lbl = f"{num}  {title}" if num else title
        pdf.cell(100, 6, safe_text(lbl), ln=0)
        if badge:
            bw = max(28, pdf.get_string_width(badge) + 10)
            bx = 200 - bw
            if btype == "success":
                pdf.set_fill_color(*CSB); pdf.set_text_color(*CS)
            elif btype == "warn":
                pdf.set_fill_color(*CWB); pdf.set_text_color(*CW)
            else:
                pdf.set_fill_color(*CDB); pdf.set_text_color(*CD)
            pdf.set_xy(bx, y + 0.5)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(bw, 5, badge, border=0, ln=0, align="C", fill=True)

    def _img(path, x, y, w, h):
        if not path or not os.path.exists(path):
            return
        pdf.set_draw_color(*CB)
        pdf.rect(x - 0.5, y - 0.5, w + 1, h + 1, style="D")
        try:
            im = cv2.imread(path)
            if im is not None:
                ho, wo = im.shape[:2]
                asp = wo / ho
                ta = w / h
                if asp > ta:
                    dw, dh = w, w / asp
                    ox, oy = 0, (h - dh) / 2
                else:
                    dh, dw = h, h * asp
                    oy, ox = 0, (w - dw) / 2
                pdf.image(path, x=x + ox, y=y + oy, w=dw, h=dh)
            else:
                pdf.image(path, x=x, y=y, w=w, h=h)
        except Exception:
            try:
                pdf.image(path, x=x, y=y, w=w, h=h)
            except Exception:
                pass

    def _tbl(y, hdrs, rows, ws):
        pdf.set_xy(10, y)
        pdf.set_draw_color(*CB)
        pdf.set_fill_color(*CN)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(hdrs):
            pdf.cell(ws[i], 6, h, border=1, fill=True, align="C")
        cy = y + 6
        for ri, row in enumerate(rows):
            pdf.set_xy(10, cy)
            bg = CLB if ri % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            pdf.set_text_color(*CN)
            for i, val in enumerate(row):
                pdf.set_font("Helvetica", "B" if i == 0 else "", 8)
                pdf.cell(ws[i], 5.5, safe_text(str(val)), border=1, fill=True, align="C" if i > 0 else "L")
            cy += 5.5
        return cy

    # ================================================================
    # PAGE 3: PRELIMINARY & HIRSCHBERG DETAIL
    # ================================================================
    pdf.add_page()
    _hdr("Detailed Measurement Appendix")

    y = 20
    _sec("6", "Preliminary Test -- Detailed Values", "MEASURED", "success", y)
    pdf.set_xy(10, y + 7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CM)
    pdf.cell(95, 4, "Corneal landmark numerical measurements", ln=0)

    y = _tbl(y + 12, ["Parameter", "Value"],
             [("Horizontal Eye Ratio (HER)", prelim_her),
              ("Vertical Eye Ratio (VER)", prelim_ver),
              ("Horizontal Squint", prelim_h_squint),
              ("Vertical Squint", prelim_v_squint)],
             [95, 95])

    if prelim_img and os.path.exists(prelim_img):
        _img(prelim_img, 25, y + 3, 160, 55)
        y += 61

    y = max(y + 4, 112)
    _sec("7", "Hirschberg Test -- Detailed Measurements", "MEASURED", "success", y)
    pdf.set_xy(10, y + 7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CM)
    pdf.cell(95, 4, "Corneal reflex coordinates and iris distances", ln=0)

    def clean_px(val):
        if not val or val == "N/A":
            return "N/A"
        s = str(val).strip()
        # remove any existing 'px' (case-insensitive)
        if s.lower().endswith("px"):
            s = s[:-2].strip()
        return f"{s} px"

    y = _tbl(y + 12, ["Measurement", "Value"],
             [("Left Vertical (LV)", clean_px(hirsch_lv)),
              ("Left Horizontal (LH)", clean_px(hirsch_lh)),
              ("Right Vertical (RV)", clean_px(hirsch_rv)),
              ("Right Horizontal (RH)", clean_px(hirsch_rh)),
              ("Left Iris White Spot", clean_px(hirsch_left_white)),
              ("Right Iris White Spot", clean_px(hirsch_right_white)),
              ("Right Vertical Dist. (RVD)", hirsch_rvd_raw),
              ("Right Horizontal Dist. (RHD)", hirsch_rhd_raw),
              ("Left Vertical Dist. (LVD)", hirsch_lvd_raw),
              ("Left Horizontal Dist. (LHD)", hirsch_lhd_raw)],
             [95, 95])

    if hirsch_notes:
        # Cap the box to the space actually available above the footer so a
        # long note list can't overflow past the page bottom (it would
        # otherwise silently overlap/clip against the footer text).
        FOOTER_SAFE_Y = 270
        available_h = max(0, FOOTER_SAFE_Y - (y + 2))
        max_lines = max(0, int((available_h - 5) / 3.5))

        notes_to_show = hirsch_notes
        truncated_count = 0
        if len(hirsch_notes) > max_lines:
            shown = max(0, max_lines - 1)  # reserve one line for the "+N more" note
            notes_to_show = hirsch_notes[:shown]
            truncated_count = len(hirsch_notes) - shown

        nh = min(5 + (len(notes_to_show) + (1 if truncated_count else 0)) * 3.5, available_h)
        pdf.set_fill_color(*CLB)
        pdf.set_draw_color(*CB)
        pdf.rect(10, y + 2, 190, nh, style="FD")
        pdf.set_fill_color(*CT)
        pdf.rect(10, y + 2, 1.5, nh, style="F")
        pdf.set_xy(14, y + 3)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*CN)
        pdf.cell(50, 4, "Additional Notes", ln=1)
        pdf.set_font("Helvetica", "", 7.5)
        for nt in notes_to_show:
            pdf.set_x(14)
            pdf.cell(180, 3.5, safe_text(nt), ln=1)
        if truncated_count:
            pdf.set_x(14)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.set_text_color(*CM)
            pdf.cell(180, 3.5, safe_text(f"... plus {truncated_count} more note(s) (see raw Hirschberg report)"), ln=1)

    _ftr()

    # ================================================================
    # PAGE 4: 9-GAZE AREAL RATIOS
    # ================================================================
    pdf.add_page()
    _hdr("Detailed Measurement Appendix")

    y = 20
    _sec("8", "9-Gaze Areal Ratios", "MEASURED", "success", y)
    pdf.set_xy(10, y + 7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CM)
    pdf.cell(190, 4, "Iris-scleral areal ratio per gaze position", ln=0)

    if areal_ratios:
        y = _tbl(y + 12, ["Gaze Position", "Areal Ratio"], areal_ratios, [95, 95])
    else:
        y += 15
        pdf.set_xy(10, y)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*CM)
        pdf.cell(190, 5, "No areal ratio data available", ln=1, align="C")
        y += 6

    if gaze_img and os.path.exists(gaze_img):
        _img(gaze_img, 15, y + 3, 180, 90)

    _ftr()

    # ================================================================
    # PAGES 5+: PER-GAZE BREAKDOWN
    # ================================================================
    if blocks:
        pdf.add_page()
        _hdr("Per-Gaze Detailed Analysis")
        yp = 20
        _sec("9", "Per-Gaze Grade & Distance Breakdown", "DETAILED", "warn", yp)
        pdf.set_xy(10, yp + 7)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*CM)
        pdf.cell(190, 4, "Grades indicate EOM involvement; distances in pixels", ln=1)
        yp += 13

        for blk in blocks:
            gn = blk['image']
            gd = gaze_directions.get(gn, gn)
            nd = len(blk.get('distances', {}))
            needed = 9 + 5 + (4 + ((nd + 1) // 2) * 3.5 if nd else 0) + 4
            if yp + needed > 270:
                _ftr()
                pdf.add_page()
                _hdr("Per-Gaze Detailed Analysis (cont.)")
                yp = 20

            pdf.set_fill_color(*CN)
            pdf.rect(10, yp, 190, 5.5, style="F")
            pdf.set_xy(14, yp + 0.8)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(100, 4, safe_text(f"{gn}  --  {gd}"), ln=0)
            yp += 7

            if blk['grades']:
                pdf.set_xy(10, yp)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(*CN)
                pdf.cell(18, 4, "Grades:", ln=0)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(*CD)
                gs = "   |   ".join([f"{k}: {v}" for k, v in blk['grades'].items()])
                pdf.cell(170, 4, gs, ln=1)
            else:
                pdf.set_xy(10, yp)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(*CM)
                pdf.cell(190, 4, "No significant grade deviation", ln=1)
            yp += 5

            if blk.get('distances'):
                items = list(blk['distances'].items())
                half = (len(items) + 1) // 2
                c1, c2 = items[:half], items[half:]
                for di in range(max(len(c1), len(c2))):
                    pdf.set_xy(12, yp)
                    pdf.set_font("Helvetica", "", 7)
                    if di < len(c1):
                        pdf.set_text_color(*CN)
                        pdf.cell(22, 3.5, c1[di][0])
                        pdf.set_text_color(*CM)
                        pdf.cell(22, 3.5, c1[di][1])
                    else:
                        pdf.cell(44, 3.5, "")
                    if di < len(c2):
                        pdf.set_text_color(*CN)
                        pdf.cell(22, 3.5, c2[di][0])
                        pdf.set_text_color(*CM)
                        pdf.cell(22, 3.5, c2[di][1])
                    yp += 3.5
            yp += 4

        # Check if the methodology section fits on the same page
        if yp + 115 <= 270:
            y = yp + 4
            same_page = True
        else:
            _ftr()
            y = 20
            same_page = False
    else:
        y = 20
        same_page = False

    # ================================================================
    # LAST PAGE: PATTERN ANALYSIS METHODOLOGY
    # ================================================================
    if not same_page:
        pdf.add_page()
        _hdr("Strabismus Pattern Analysis -- Methodology")

    _sec("10", "Pattern Analysis Methodology & Raw Values", "ANALYSIS", "warn", y)
    pdf.set_xy(10, y + 7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CM)
    pdf.cell(190, 4, "Detailed breakdown of the pattern detection algorithm", ln=1)

    my = y + 13
    pdf.set_fill_color(*CLB)
    pdf.set_draw_color(*CB)
    pdf.rect(10, my, 190, 48, style="FD")
    pdf.set_fill_color(*CT)
    pdf.rect(10, my, 1.5, 48, style="F")

    pdf.set_xy(14, my + 2)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*CN)
    pdf.cell(180, 4, "Deviation Formula", ln=1)
    pdf.set_xy(14, my + 7)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.multi_cell(180, 3.5, safe_text(
        "Deviation = (R_Lateral - R_Medial) + (L_Lateral - L_Medial)\n\n"
        "Averaged across gaze groups:\n"
        "  Upgaze: gaze_1, gaze_2, gaze_3\n"
        "  Downgaze: gaze_7, gaze_8, gaze_9\n"
        "  Primary: gaze_5"))

    pdf.set_xy(14, my + 28)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*CN)
    pdf.cell(180, 4, "Pattern Detection Criteria", ln=1)
    pdf.set_xy(14, my + 33)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.multi_cell(180, 3.5, safe_text(
        "Diff >= 5 and Upgaze > Downgaze: V-pattern\n"
        "Diff >= 5 and Upgaze < Downgaze: A-pattern\n"
        "Upgaze > Primary > Downgaze: Y-pattern\n"
        "Downgaze > Primary > Upgaze: Reverse Y-pattern\n"
        "Otherwise: No significant pattern"))

    ry = my + 54
    _sec("", "Raw Per-Gaze Deviation Values", "", "success", ry)

    def _gdev(dist):
        try:
            return (float(dist.get("R_Lateral", 0)) - float(dist.get("R_Medial", 0))) + \
                   (float(dist.get("L_Lateral", 0)) - float(dist.get("L_Medial", 0)))
        except Exception:
            return 0

    up_devs = [_gdev(b['distances']) for b in blocks if b['image'] in ["gaze_1.jpg", "gaze_2.jpg", "gaze_3.jpg"]]
    dn_devs = [_gdev(b['distances']) for b in blocks if b['image'] in ["gaze_7.jpg", "gaze_8.jpg", "gaze_9.jpg"]]
    pr_devs = [_gdev(b['distances']) for b in blocks if b['image'] == "gaze_5.jpg"]

    pdf.set_xy(10, ry + 8)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*CN)
    pdf.cell(25, 4, "Upgaze:", ln=0)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(125, 4, safe_text("   ".join([f"gaze_{i+1}: {v:.2f}" for i, v in enumerate(up_devs)])), ln=0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 4, f"Avg: {avg_up:.2f}", ln=1, align="R")

    pdf.set_xy(10, ry + 14)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*CN)
    pdf.cell(25, 4, "Downgaze:", ln=0)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(125, 4, safe_text("   ".join([f"gaze_{i+7}: {v:.2f}" for i, v in enumerate(dn_devs)])), ln=0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 4, f"Avg: {avg_down:.2f}", ln=1, align="R")

    pdf.set_xy(10, ry + 20)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*CN)
    pdf.cell(25, 4, "Primary:", ln=0)
    pdf.set_font("Helvetica", "", 8)
    pv = pr_devs[0] if pr_devs else 0
    pdf.cell(125, 4, f"gaze_5: {pv:.2f}", ln=0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 4, f"Value: {primary_dev:.2f}", ln=1, align="R")

    pdf.set_xy(10, ry + 26)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*CN)
    pdf.cell(25, 4, "Difference:", ln=0)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(125, 4, f"Upgaze - Downgaze = {diff:.2f}", ln=1)

    rx = ry + 34
    if "detected" in pattern_result.lower():
        pdf.set_fill_color(*CDB)
        pdf.set_draw_color(*CD)
        rc = CD
    else:
        pdf.set_fill_color(*CSB)
        pdf.set_draw_color(*CS)
        rc = CS
    pdf.rect(10, rx, 190, 10, style="FD")
    pdf.set_xy(12, rx + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*rc)
    pdf.cell(186, 6, safe_text(f"Final Pattern Result: {pattern_result}"), align="C")

    _ftr()
