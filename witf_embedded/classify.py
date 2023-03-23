from collections import deque
import queue
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
    max_num_hands=1,
    min_detection_confidence=constants.MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
)

# Globals
handedness_in = None
base_selected_frame_id = None
frame_buffer = deque(maxlen=constants.FRAME_BUFFER_SIZE)
flush_buffer = False
out_frame_count = -1
action_segment = constants.ActionSegment.OUT

# Text Stuff
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 2
color = (255, 255, 255)
text_size = cv.getTextSize(action_segment.name, font, font_scale, 1)[0]


def classify(frame, width, height, top, bottom, fridge_left, debug=False, no_convert=False):
    # Setup
    global action_segment, handedness_in, base_selected_frame_id, flush_buffer, out_frame_count

    # Run hand detection
    frame.flags.writeable = False
    if not no_convert:
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    resized_frame = cv.resize(frame, (int(width/10), int(height/10)))
    s = time.perf_counter()
    results = hands.process(resized_frame)
    f = time.perf_counter()
    #print('p2', f-s)

    frame.flags.writeable = True
    frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

    # Update frame buffer
    add_frame_to_buffer(frame)

    # Parse results
    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                results.multi_handedness):
            prev_action_segment = action_segment
            
            # Hand in fridge
            if (hand_in_fridge(hand_landmarks, width, top, fridge_left)):
                handedness_in = handedness.classification[0].label
                action_segment = constants.ActionSegment.IN

                # If hand goes into the fridge capture this frame
                if prev_action_segment == constants.ActionSegment.OUT:
                    flush_buffer = True

            # If hand not in fridge && its the same hand that was previously inside the fridge
            elif (handedness_in == handedness.classification[0].label):
                action_segment = constants.ActionSegment.OUT

                # If hand goes out of the fridge capture this frame
                if prev_action_segment == constants.ActionSegment.IN:
                    out_frame_count = constants.FRAME_BUFFER_SIZE                 

            # Draw handlandmarks
            if debug:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )

    if debug:
        cv.line(frame, (top['x'], top['y']), (bottom['x'], bottom['y']), (0, 255, 0), 2, lineType=cv.LINE_AA)
        draw_label(frame)

    if flush_buffer:
        selected_frames = []
        selected_frame_ids = []

        while frame_buffer:
            uid, selected_frame = frame_buffer.popleft()

            selected_frames.append(selected_frame)
            selected_frame_ids.append(uid)

        flush_buffer = False

        return frame, selected_frames, selected_frame_ids

    return frame, None, None


def hand_in_fridge(hand_landmarks, width, top, fridge_left):
    hand_left = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x * width < top['x']
    return hand_left == fridge_left # Hand in fridge if both are in the left side or right side


def draw_label(frame):
    # Define the position of the text
    x = 0
    y = text_size[1] + 10
    # Draw a rectangle around the text
    cv.rectangle(frame, (x, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
    # Put the text in the frame
    cv.putText(frame, action_segment.name, (x + 5, y), font, font_scale, color, 1, cv.LINE_AA)


def generate_frame_id(action_segment, clean=False):
    global base_selected_frame_id

    if clean or base_selected_frame_id is None:
        base_selected_frame_id = str(uuid.uuid4())[:8]

    uid = f'{int(time.time())}_{base_selected_frame_id}_{action_segment.name}'
    return uid
    

def add_frame_to_buffer(frame):
    global flush_buffer, out_frame_count
    frame = frame.copy()

    # Frames going in 
    if out_frame_count < 0:
        uid = generate_frame_id(constants.ActionSegment.IN)
        frame_buffer.append((uid, frame))

    # frames going out
    else:
        uid = generate_frame_id(constants.ActionSegment.OUT)
        frame_buffer.append((uid, frame))
        out_frame_count -= 1

        # When finished reset flags and generate new base_id
        if out_frame_count == 0:
            flush_buffer = True
            out_frame_count = -1
            generate_frame_id(action_segment, True)
    