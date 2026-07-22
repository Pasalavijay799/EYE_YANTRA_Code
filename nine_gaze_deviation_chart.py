import math
import os
import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
_face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
L_MED, L_LAT = 362, 263
R_MED, R_LAT = 133, 33

# Iris diameter is a stable anatomical constant, used as an in-image ruler to get mm-per-pixel.
IRIS_DIAMETER_MM = 11.7
# Whole-eyeball radius (not corneal radius) - correct for iris/globe rotation, unlike the
# corneal-reflex-specific Hirschberg conversion which uses corneal radius (~7.8mm) instead.
EYEBALL_RADIUS_MM = 12.0


def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _landmark_xy(landmarks, idx, w, h):
    lm = landmarks[idx]
    return (lm.x * w, lm.y * h)


def _iris_center_and_radius(landmarks, indices, w, h):
    pts = [_landmark_xy(landmarks, i, w, h) for i in indices]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    center = (cx, cy)
    radius = sum(_dist(center, p) for p in pts) / len(pts)
    return center, radius


def _measure_raw(image_path):
    """Returns (s_px, mm_per_px) for one gaze photo, or (None, None) if no face found.

    s_px follows the same sign convention as before: positive skews toward the
    medial corner on both eyes (esotropic tendency), negative skews lateral
    (exotropic tendency). This is the RAW, single-photo value - not yet a
    deviation angle, since it also carries each photo's baseline head pose /
    angle kappa, which is why it must be compared against the primary-gaze
    value rather than converted to degrees directly (see build_cross_chart).
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return None, None
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None, None
    landmarks = results.multi_face_landmarks[0].landmark

    left_iris_center, left_iris_radius = _iris_center_and_radius(landmarks, LEFT_IRIS, w, h)
    right_iris_center, right_iris_radius = _iris_center_and_radius(landmarks, RIGHT_IRIS, w, h)

    L_med = _landmark_xy(landmarks, L_MED, w, h)
    L_lat = _landmark_xy(landmarks, L_LAT, w, h)
    R_med = _landmark_xy(landmarks, R_MED, w, h)
    R_lat = _landmark_xy(landmarks, R_LAT, w, h)

    R_Lateral = _dist(right_iris_center, R_lat)
    R_Medial = _dist(right_iris_center, R_med)
    L_Lateral = _dist(left_iris_center, L_lat)
    L_Medial = _dist(left_iris_center, L_med)

    iris_radius_px = (left_iris_radius + right_iris_radius) / 2
    mm_per_px = IRIS_DIAMETER_MM / (2 * iris_radius_px) if iris_radius_px > 0 else 0

    s_px = (R_Lateral - R_Medial) + (L_Lateral - L_Medial)
    return s_px, mm_per_px


def _measure_primary_asymmetry(image_path):
    """Absolute (single-photo) misalignment indicator for the primary-gaze photo only.

    Unlike Up/Down/Left/Right (measured as a delta relative to primary - see
    _measure_raw / build_cross_chart, untouched by this function), primary gaze has
    no "other photo" to compare against. Comparing it to itself is always exactly
    zero and carries no information. Instead, this compares each eye's own
    lateral-vs-medial balance against the OTHER eye, within this one photo - the
    same "compare within a single frame" principle behind the Hirschberg
    reflex-vs-pupil measurement, just using eye-to-eye symmetry instead.

    Caveat: this can only detect ASYMMETRIC misalignment (one eye differing from
    the other). A symmetric/bilateral deviation - both eyes off by the same amount
    in the same direction - would still read as zero here, since there's no
    external "true straight ahead" reference, only the two eyes compared to
    each other.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return None, None
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None, None
    landmarks = results.multi_face_landmarks[0].landmark

    left_iris_center, left_iris_radius = _iris_center_and_radius(landmarks, LEFT_IRIS, w, h)
    right_iris_center, right_iris_radius = _iris_center_and_radius(landmarks, RIGHT_IRIS, w, h)

    L_med = _landmark_xy(landmarks, L_MED, w, h)
    L_lat = _landmark_xy(landmarks, L_LAT, w, h)
    R_med = _landmark_xy(landmarks, R_MED, w, h)
    R_lat = _landmark_xy(landmarks, R_LAT, w, h)

    R_Lateral = _dist(right_iris_center, R_lat)
    R_Medial = _dist(right_iris_center, R_med)
    L_Lateral = _dist(left_iris_center, L_lat)
    L_Medial = _dist(left_iris_center, L_med)

    iris_radius_px = (left_iris_radius + right_iris_radius) / 2
    mm_per_px = IRIS_DIAMETER_MM / (2 * iris_radius_px) if iris_radius_px > 0 else 0

    asym_px = (R_Lateral - R_Medial) - (L_Lateral - L_Medial)
    return asym_px, mm_per_px


def build_cross_chart(person_folder):
    """person_folder: path to the folder containing gaze_1.jpg .. gaze_9.jpg

    Returns a dict with keys up/down/left/right/primary, matching the classic
    5-position prism cover test cross layout (diagonals gaze_1/3/7/9 aren't used here).

    Each value is the deviation RELATIVE TO PRIMARY GAZE - not an absolute per-photo
    value. This mirrors the principle behind the Hirschberg conversion (reflex minus
    pupil center, in the same frame): comparing against a same-conditions reference
    cancels out each photo's baseline head pose / angle kappa, which a raw absolute
    value does not.
    """
    positions = {
        "up": "gaze_2.jpg",
        "down": "gaze_8.jpg",
        "left": "gaze_4.jpg",
        "right": "gaze_6.jpg",
        "primary": "gaze_5.jpg",
    }
    raw = {}
    for label, filename in positions.items():
        path = os.path.join(person_folder, filename)
        raw[label] = _measure_raw(path) if os.path.exists(path) else (None, None)

    primary_s_px, primary_mm_per_px = raw.get("primary", (None, None))

    chart = {}
    for label, (s_px, mm_per_px) in raw.items():
        if s_px is None or primary_s_px is None:
            chart[label] = None
            continue

        if label == "primary":
            # Absolute eye-to-eye asymmetry within the primary photo itself -
            # see _measure_primary_asymmetry. Up/Down/Left/Right below are
            # untouched and still use the delta-from-primary approach.
            primary_path = os.path.join(person_folder, positions["primary"])
            asym_px, asym_mm_per_px = _measure_primary_asymmetry(primary_path)
            if asym_px is None:
                chart[label] = None
                continue
            delta_px = asym_px
            mm_per_px = asym_mm_per_px
        else:
            delta_px = s_px - primary_s_px

        delta_mm = delta_px * mm_per_px
        degrees = math.degrees(delta_mm / EYEBALL_RADIUS_MM)
        pd = 100 * math.tan(math.radians(degrees))

        if abs(degrees) < 0.5:
            direction = "Ortho"
        else:
            direction = "ET" if degrees > 0 else "XT"

        chart[label] = {
            "s_px": delta_px,
            "s_mm": delta_mm,
            "degrees": degrees,
            "pd": pd,
            "direction": direction,
        }
    return chart


if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    chart = build_cross_chart(folder)
    for k, v in chart.items():
        print(k, v)
