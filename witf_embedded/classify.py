import time
import mediapipe as mp
import cv2 as cv
import uuid
import constants

# Load model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=constants.MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
)

# Text Stuff
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 2
action_segment = constants.ActionSegment.OUT
color = (255, 255, 255)
text_size = cv.getTextSize(action_segment.name, font, font_scale, 1)[0]

# Globals
handedness_in = None
base_selected_frame_id = None

def classify(frame, width, height, top, bottom, debug=False):
    # Setup
    global action_segment, handedness_in
    selected_frame_id = None
    selected_frame = None

    # Run hand detection
    frame.flags.writeable = False
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frame)
    frame.flags.writeable = True
    frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

    # Parse results
    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                results.multi_handedness):
            prev_action_segment = action_segment
            
            # Hand in fridge
            if (hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x * width > top['x']):
                handedness_in = handedness.classification[0].label
                action_segment = constants.ActionSegment.IN

                # If hand goes into the fridge capture this frame
                if prev_action_segment == constants.ActionSegment.OUT:
                    # When hand goes in this is a new action segment so reset the base frame id
                    base_selected_frame_id = None
                    selected_frame_id = generate_frame_id(prev_action_segment)
                    base_selected_frame_id = selected_frame_id[:8]

                    selected_frame = frame.copy()
                    draw_label(selected_frame)

            # If hand not in fridge && its the same hand that was previously inside the fridge
            elif (handedness_in == handedness.classification[0].label):
                action_segment = constants.ActionSegment.OUT

                # If hand goes out of the fridge capture this frame
                if prev_action_segment == constants.ActionSegment.IN:
                    selected_frame_id = generate_frame_id(prev_action_segment)

                    selected_frame = frame.copy()
                    draw_label(selected_frame)
                    selected_frame_id = generate_frame_id(prev_action_segment)

            # Draw handlandmarks
            if debug:
                mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

    if debug:
        cv.line(frame, (top['x'], top['y']), (bottom['x'], bottom['y']), (0, 255, 0), 2, lineType=cv.LINE_AA)
        # print("HAND", handedness_in)
        draw_label(frame)

    return frame, selected_frame, selected_frame_id


def draw_label(frame):
    # Define the position of the text
    x = 0
    y = text_size[1] + 10
    # Draw a rectangle around the text
    cv.rectangle(frame, (x, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
    # Put the text in the frame
    cv.putText(frame, action_segment.name, (x + 5, y), font, font_scale, color, 1, cv.LINE_AA)


def generate_frame_id(prev_action_segment):
    global base_selected_frame_id
    if base_selected_frame_id is None:
        base_selected_frame_id = str(uuid.uuid4())[:8]

    uid = f'{base_selected_frame_id}_{int(time.time())}_{prev_action_segment.name}'
    return uid
    