import cv2
import mediapipe as mp
import time

# -----------------------------
# MediaPipe setup
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh

cap = cv2.VideoCapture(0)

# -----------------------------
# STATE MACHINE
# -----------------------------
state = "IDLE"

# -----------------------------
# Stability tracking
# -----------------------------
stable_presence  = 0
stable_absence   = 0
person_confirmed = False
center_frames    = 0

# -----------------------------
# Target Lock
# -----------------------------
locked_face_center = None
lock_lost_frames   = 0
LOCK_TIMEOUT       = 30

# -----------------------------
# Clean Code: Configuration Thresholds
# -----------------------------
STABLE_PRESENCE_THRESHOLD = 15
STABLE_ABSENCE_THRESHOLD  = 20
CENTER_ENGAGE_THRESHOLD   = 20
SWITCH_DISTANCE_THRESHOLD = 150

# -----------------------------
# Output for NLP team
# -----------------------------
robot_output = {
    "visitor_present": False,
    "state": "IDLE"
}

# -----------------------------
# EVALUATION METRICS
# -----------------------------
eval_metrics = {
    # FPS
    "fps"                    : 0,
    "frame_count"            : 0,
    "start_time"             : time.time(),

    # Detection
    "total_frames"           : 0,
    "detected_frames"        : 0,

    # State Transition
    "idle_start_time"        : time.time(),
    "engaged_time"           : None,
    "last_transition_sec"    : None,

    # Lock Stability
    "selection_switches"     : 0,
    "last_selected_center"   : None,

    # Multi-Person
    "multi_person_frames"    : 0,
    "correct_selection_frames": 0,
}


# -----------------------------
# BEST FACE SORTED BY SIZE
# -----------------------------
def get_faces_sorted_by_size(faces, frame_w, frame_h):
    scored = []
    for face in faces:
        xs = [lm.x * frame_w for lm in face.landmark]
        ys = [lm.y * frame_h for lm in face.landmark]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        scored.append((area, face))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [face for _, face in scored]


# -----------------------------
# FIND LOCKED FACE
# -----------------------------
def find_locked_face(faces, frame_w, frame_h, locked_center, max_dist=100):
    if locked_center is None:
        return None
    lx, ly = locked_center
    closest = None
    closest_dist = max_dist
    for face in faces:
        xs = [lm.x * frame_w for lm in face.landmark]
        ys = [lm.y * frame_h for lm in face.landmark]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
        if dist < closest_dist:
            closest_dist = dist
            closest = face
    return closest


# -----------------------------
# GET FACE CENTER
# -----------------------------
def get_face_center(face, frame_w, frame_h):
    xs = [lm.x * frame_w for lm in face.landmark]
    ys = [lm.y * frame_h for lm in face.landmark]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


# -----------------------------
# DRAW EVALUATION PANEL
# -----------------------------
def draw_eval_panel(frame, metrics, person_count):
    # Semi-transparent background for the panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (430, 0), (640, 210), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Calculate detection rate
    total = metrics["total_frames"]
    detected = metrics["detected_frames"]
    det_rate = (detected / total * 100) if total > 0 else 0

    # Calculate selection stability
    switches = metrics["selection_switches"]
    stability = max(0, 100 - (switches * 5))

    # Calculate correct selection rate
    multi = metrics["multi_person_frames"]
    correct = metrics["correct_selection_frames"]
    sel_acc = (correct / multi * 100) if multi > 0 else 100

    transition = f"{metrics['last_transition_sec']:.1f}s" if metrics["last_transition_sec"] else "N/A"

    lines = [
        ("-- EVALUATION --",  (255, 255, 255)),
        (f"FPS:        {metrics['fps']:.1f}",          (0, 255, 0)),
        (f"Detection:  {det_rate:.1f}%",               (0, 255, 255)),
        (f"Transition: {transition}",                   (0, 200, 255)),
        (f"Stability:  {stability:.0f}%",              (0, 255, 200)),
        (f"Selection:  {sel_acc:.1f}%",                (255, 200, 0)),
        (f"Switches:   {switches}",                    (100, 100, 255)),
    ]

    for i, (text, color) in enumerate(lines):
        cv2.putText(frame, text, (435, 20 + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


# -----------------------------
# MAIN LOOP
# -----------------------------
with mp_face_mesh.FaceMesh(
    max_num_faces=10,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as face_mesh:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_start = time.time()

        frame = cv2.resize(frame, (640, 480))
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = face_mesh.process(rgb)

        person_count   = 0
        main_direction = "N/A"

        # Update total frames
        eval_metrics["total_frames"] += 1

        # -----------------------------
        # FACE DETECTION + TARGET LOCK
        # -----------------------------
        if results.multi_face_landmarks:
            person_count = len(results.multi_face_landmarks)
            eval_metrics["detected_frames"] += 1

            sorted_faces = get_faces_sorted_by_size(results.multi_face_landmarks, w, h)

            # Look for the previously locked face
            face = find_locked_face(sorted_faces, w, h, locked_face_center)

            if face is None:
                # If locked face is not found, select the largest face (closest to robot)
                face = sorted_faces[0]

            # ----- LOCK STABILITY EVALUATION -----
            new_center = get_face_center(face, w, h)
            if eval_metrics["last_selected_center"] is not None:
                lx, ly = eval_metrics["last_selected_center"]
                dist = ((new_center[0] - lx) ** 2 + (new_center[1] - ly) ** 2) ** 0.5
                if dist > SWITCH_DISTANCE_THRESHOLD:  # Selected target changed suddenly
                    eval_metrics["selection_switches"] += 1
            eval_metrics["last_selected_center"] = new_center

            # ----- MULTI PERSON SELECTION EVALUATION -----
            if person_count > 1:
                eval_metrics["multi_person_frames"] += 1
                # Correct if selected is the largest or second largest
                if face is sorted_faces[0] or (len(sorted_faces) >= 2 and face is sorted_faces[1]):
                    eval_metrics["correct_selection_frames"] += 1

            # Update locked face center
            xs = [lm.x * w for lm in face.landmark]
            ys = [lm.y * h for lm in face.landmark]
            locked_face_center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            lock_lost_frames = 0

            # Draw all faces
            for i, f in enumerate(sorted_faces):
                fxs = [lm.x * w for lm in f.landmark]
                fys = [lm.y * h for lm in f.landmark]
                x1, y1 = int(min(fxs)), int(min(fys))
                x2, y2 = int(max(fxs)), int(max(fys))

                if f is face:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(frame, "SELECTED", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                elif i == 1:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(frame, "BACKUP", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 1)
                    cv2.putText(frame, "OTHER", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Calculate looking direction
            nose  = face.landmark[1]
            left  = face.landmark[33]
            right = face.landmark[263]
            x_nose   = nose.x * w
            center_x = ((left.x + right.x) / 2) * w
            error    = (x_nose - center_x) / w

            if error < -0.05:
                main_direction = "RIGHT"
            elif error > 0.05:
                main_direction = "LEFT"
            else:
                main_direction = "CENTER"

        else:
            lock_lost_frames += 1
            if lock_lost_frames > LOCK_TIMEOUT:
                locked_face_center = None

        # -----------------------------
        # STABILITY FILTER
        # -----------------------------
        if person_count > 0:
            stable_presence += 1
            stable_absence = 0
        else:
            stable_absence += 1
            stable_presence = 0

        if stable_presence > STABLE_PRESENCE_THRESHOLD:
            person_confirmed = True

        if stable_absence > STABLE_ABSENCE_THRESHOLD:
            person_confirmed = False
            state = "IDLE"
            center_frames = 0
            locked_face_center = None

        # -----------------------------
        # INTENT DETECTION
        # -----------------------------
        if main_direction == "CENTER":
            center_frames += 1
        else:
            center_frames = 0

        # -----------------------------
        # STATE MACHINE
        # -----------------------------
        if state == "IDLE":
            cv2.putText(frame, "STATE: IDLE", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            robot_output["visitor_present"] = False
            robot_output["state"] = "IDLE"
            eval_metrics["idle_start_time"] = time.time()

            if person_confirmed:
                state = "OBSERVING"

        elif state == "OBSERVING":
            cv2.putText(frame, "STATE: OBSERVING", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            robot_output["visitor_present"] = True
            robot_output["state"] = "OBSERVING"

            if center_frames > CENTER_ENGAGE_THRESHOLD:
                state = "ENGAGED"

        elif state == "ENGAGED":
            # Safety check: Ensure person is actually in the frame before triggering NLP
            if person_count > 0:
                cv2.putText(frame, "STATE: ENGAGED", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                robot_output["visitor_present"] = True
                robot_output["state"] = "ENGAGED"

                # ----- STATE TRANSITION EVALUATION -----
                eval_metrics["last_transition_sec"] = time.time() - eval_metrics["idle_start_time"]

                print("✅ Visitor engaged — sending to NLP...")
                print(f"📤 Output: {robot_output}")
                print(f"⏱️ Transition time: {eval_metrics['last_transition_sec']:.2f}s")

                state = "TALKING"
            else:
                # If person disappeared exactly at engagement moment, revert to observing
                state = "OBSERVING"
                center_frames = 0

        elif state == "TALKING":
            cv2.putText(frame, "STATE: TALKING", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            robot_output["visitor_present"] = True
            robot_output["state"] = "TALKING"

            if not person_confirmed:
                state = "IDLE"

        # -----------------------------
        # FPS CALCULATION
        # -----------------------------
        eval_metrics["frame_count"] += 1
        elapsed = time.time() - eval_metrics["start_time"]
        if elapsed > 0:
            eval_metrics["fps"] = eval_metrics["frame_count"] / elapsed

        # -----------------------------
        # UI
        # -----------------------------
        cv2.putText(frame, f"Persons: {person_count}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Direction: {main_direction}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Center Frames: {center_frames}", (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if lock_lost_frames > 0:
            cv2.putText(frame, f"Waiting: {lock_lost_frames}/{LOCK_TIMEOUT}", (20, 170),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # Evaluation Panel
        draw_eval_panel(frame, eval_metrics, person_count)

        cv2.imshow("Robot Guide System", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

# -----------------------------
# FINAL REPORT in terminal
# -----------------------------
total    = eval_metrics["total_frames"]
detected = eval_metrics["detected_frames"]
multi    = eval_metrics["multi_person_frames"]
correct  = eval_metrics["correct_selection_frames"]

print("\n" + "="*40)
print("       FINAL EVALUATION REPORT")
print("="*40)
print(f"Total Frames       : {total}")
print(f"FPS (avg)          : {eval_metrics['fps']:.1f}")
print(f"Detection Rate     : {detected/total*100:.1f}% ({detected}/{total})")
print(f"Transition Time    : {eval_metrics['last_transition_sec']:.2f}s" if eval_metrics['last_transition_sec'] else "Transition Time    : N/A")
print(f"Lock Stability     : {max(0, 100 - eval_metrics['selection_switches']*5):.0f}%")
print(f"Selection Accuracy : {correct/multi*100:.1f}%" if multi > 0 else "Selection Accuracy : N/A (no multi-person)")
print(f"Selection Switches : {eval_metrics['selection_switches']}")
print("="*40)

cap.release()
cv2.destroyAllWindows()