# import time
# import mediapipe as mp
# import cv2 as cv
# import uuid
# import constants

# from collections import deque
# from constants import LOGGER as logger


# # Load model
# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles

# hands = mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=2,
#     min_detection_confidence=constants.MIN_DETECTION_CONFIDENCE,
#     min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
# )

# # Globals
# handedness_in = None
# base_selected_frame_id = None
# frame_buffer = deque(maxlen=constants.FRAME_BUFFER_SIZE)
# flush_buffer = False
# out_frame_count = -1
# action_segment = constants.ActionSegment.OUT
# hand_already_in_fridge = False

# # Text Stuff
# font = cv.FONT_HERSHEY_SIMPLEX
# font_scale = 2
# color = (255, 255, 255)
# text_size = cv.getTextSize(action_segment.name, font, font_scale, 1)[0]


# def classify(frame, width, height, top, bottom, fridge_left, debug=False, no_convert=False):
#     # Setup
#     global action_segment, handedness_in, base_selected_frame_id, flush_buffer, out_frame_count, hand_already_in_fridge

#     # Run hand detection
#     frame.flags.writeable = False
#     if not no_convert:
#         frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
#     resized_frame = cv.resize(frame, (int(width/8), int(height/8)))
#     s = time.perf_counter()
#     results = hands.process(resized_frame)
#     f = time.perf_counter()
#     #logger.debug('Hands processing time: {:.3f}s'.format(f - s))

#     frame.flags.writeable = True
#     frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

#     # Update frame buffer
#     add_frame_to_buffer(frame)

#     # Parse results
#     if results.multi_hand_landmarks:
#         for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
#                                                 results.multi_handedness):
#             prev_action_segment = action_segment
            
#             # Hand in fridge
#             if (hand_in_fridge(hand_landmarks, width, top, fridge_left)):
#                 if not hand_already_in_fridge:
#                     handedness_in = handedness.classification[0].label
#                     action_segment = constants.ActionSegment.IN
#                     #logger.debug(f'Handedness in: {handedness_in}')

#                     # If hand goes into the fridge then flush the buffer
#                     if prev_action_segment == constants.ActionSegment.OUT:
#                         flush_buffer = True

#                     hand_already_in_fridge = True

#             # If hand not in fridge && its the same hand that was previously inside the fridge
#             elif (handedness_in == handedness.classification[0].label):
#                 action_segment = constants.ActionSegment.OUT
#                 #logger.debug(f'Handedness out: {handedness_in}')

#                 # If hand goes out of the fridge, start capturing out frames in buffer
#                 if prev_action_segment == constants.ActionSegment.IN:
#                     out_frame_count = constants.FRAME_BUFFER_SIZE       

#                 hand_already_in_fridge = False          

#             # Draw handlandmarks
#             if debug:
#                 mp_drawing.draw_landmarks(
#                     frame,
#                     hand_landmarks,
#                     mp_hands.HAND_CONNECTIONS,
#                     mp_drawing_styles.get_default_hand_landmarks_style(),
#                     mp_drawing_styles.get_default_hand_connections_style()
#                 )

#     if debug:
#         cv.line(frame, (top['x'], top['y']), (bottom['x'], bottom['y']), (0, 255, 0), 2, lineType=cv.LINE_AA)
#         draw_label(frame)

#     if flush_buffer:
#         selected_frames = []
#         selected_frame_ids = []

#         logger.debug(f'Flushing buffer for group id {frame_buffer[0][0]}')
#         while frame_buffer:
#             uid, selected_frame = frame_buffer.popleft()

#             selected_frames.append(selected_frame)
#             selected_frame_ids.append(uid)

#         flush_buffer = False

#         return frame, selected_frames, selected_frame_ids

#     return frame, None, None


# def hand_in_fridge(hand_landmarks, width, top, fridge_left):
#     hand_left = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x * width < top['x']
#     return hand_left == fridge_left # Hand in fridge if both are in the left side or right side


# def draw_label(frame):
#     # Define the position of the text
#     x = 0
#     y = text_size[1] + 10
#     # Draw a rectangle around the text
#     cv.rectangle(frame, (x, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
#     # Put the text in the frame
#     cv.putText(frame, action_segment.name, (x + 5, y), font, font_scale, color, 1, cv.LINE_AA)


# def generate_frame_id(action_segment, clean=False):
#     global base_selected_frame_id

#     if clean or base_selected_frame_id is None:
#         base_selected_frame_id = str(uuid.uuid4())[:8]

#     uid = f'{int(time.time())}_{base_selected_frame_id}_{action_segment.name}'
#     return uid
    

# def add_frame_to_buffer(frame):
#     global flush_buffer, out_frame_count
#     frame = frame.copy()

#     # Adding in frames to buffer
#     if out_frame_count < 0:
#         uid = generate_frame_id(constants.ActionSegment.IN)
#         frame_buffer.append((uid, frame))

#     # Adding out frames to buffer
#     else:
#         uid = generate_frame_id(constants.ActionSegment.OUT)
#         frame_buffer.append((uid, frame))
#         out_frame_count -= 1

#         # When finished reset flags and generate new base_id
#         if out_frame_count == 0:
#             flush_buffer = True
#             out_frame_count = -1
#             generate_frame_id(action_segment, True)
    

import sys
import time
import mediapipe as mp
import cv2 as cv
import uuid
import constants

from collections import deque
from constants import LOGGER as logger


# Load model
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=constants.STATIC_IMAGE_MODE,
    max_num_hands=constants.MAX_NUM_HANDS,
    min_detection_confidence=constants.MIN_DETECTION_CONFIDENCE,
    min_tracking_confidence=constants.MIN_TRACKING_CONFIDENCE,
)

# Globals
handedness_in = None
base_output_selected_frame_ids = deque()
frame_buffer = deque(maxlen=constants.FRAME_BUFFER_SIZE)
flush_buffer = None
out_frame_count = -1
action_segment = constants.ActionSegment.OUT
hand_already_in_fridge = False

# Text Stuff
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 2
color = (255, 255, 255)
text_size = cv.getTextSize(action_segment.name, font, font_scale, 1)[0]


def classify(frame, width, height, top, bottom, fridge_left, debug=False, no_convert=False):
    # Setup
    global action_segment, handedness_in, base_selected_frame_id, flush_buffer, out_frame_count, hand_already_in_fridge

    # Run hand detection
    frame.flags.writeable = False
    if not no_convert:
        try:
            assert(frame is not None)
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        except Exception as e:
            print("Error",e)
            sys.exit()

    resized_frame = cv.resize(frame, (int(width/constants.DOWNSCALE_FACTOR), int(height/constants.DOWNSCALE_FACTOR)))
    s = time.perf_counter()
    results = hands.process(resized_frame)
    f = time.perf_counter()
    frame.flags.writeable = True
    frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

    # Update frame buffer
    add_frame_to_buffer(frame)

    prev_action_segment = action_segment
    # Parse results
    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                results.multi_handedness):
            
            # Filter out small hands or hands in the background
            if should_ignore_hand(hand_landmarks, height):
                logger.debug('[IGNORING HAND]')
                continue

            # Check if hand in fridge
            if (hand_in_fridge(hand_landmarks, width, top)):
                if not hand_already_in_fridge:
                    handedness_in = handedness.classification[0].label
                    action_segment = constants.ActionSegment.IN

                    # If hand goes into the fridge then flush the buffer
                    if prev_action_segment == constants.ActionSegment.OUT:
                        logger.info(f'[EVENT][HAND-IN]')
                        flush_buffer = constants.Flush.IN

                    hand_already_in_fridge = True

            # If hand not in fridge && its the same hand that was previously inside the fridge
            elif (handedness_in == handedness.classification[0].label):
                action_segment = constants.ActionSegment.OUT

                # If hand goes out of the fridge, start capturing out frames in buffer
                if prev_action_segment == constants.ActionSegment.IN:
                    logger.info(f'[EVENT][HAND-OUT]')
                    out_frame_count = constants.FRAME_BUFFER_SIZE       

                hand_already_in_fridge = False          

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

    if flush_buffer == constants.Flush.IN or flush_buffer == constants.Flush.OUT:
        s = time.perf_counter()
        if flush_buffer == constants.Flush.IN:
            uid = generate_uid()
            base_output_selected_frame_ids.append(uid)
            action_tag = constants.ActionSegment.IN.name
            logger.info(f'[EVENT][FLUSH-IN]: Flushing buffer for group id {uid}')
        else:
            uid = base_output_selected_frame_ids.popleft()
            action_tag = constants.ActionSegment.OUT.name
            logger.info(f'[EVENT][FLUSH-OUT]: Flushing buffer for group id {uid}')

        selected_frames = []
        selected_frame_ids = []

        temp_arr = list(frame_buffer)
        for frame_time, f in temp_arr:
            selected_frames.append(f)
            selected_frame_ids.append(f'{frame_time}_{uid}_{action_tag}')

        flush_buffer = None
        logger.debug(f'[PERFORMANCE][PROCESS TIME]: Flush time {time.perf_counter() - s}')

        return frame, selected_frames, selected_frame_ids

    return frame, None, None


def hand_in_fridge(hand_landmarks, width, top):
    return any((landmark.x * width > top['x']) for landmark in hand_landmarks.landmark)


def draw_label(frame):
    # Define the position of the text
    x = 0
    y = text_size[1] + 10
    # Draw a rectangle around the text
    cv.rectangle(frame, (x, y - text_size[1] - 10), (x + text_size[0] + 10, y + 10), (0, 0, 0), -1)
    # Put the text in the frame
    cv.putText(frame, action_segment.name, (x + 5, y), font, font_scale, color, 1, cv.LINE_AA)


def should_ignore_hand(hand_landmarks, height):
    def get_highest_point_value(hand_landmarks):
        return min(hand_landmarks.landmark, key=lambda p: p.y)
    
    def get_lowest_point_value(hand_landmarks):
        return max(hand_landmarks.landmark, key=lambda p: p.y)

    top = get_highest_point_value(hand_landmarks).y * height
    bottom = get_lowest_point_value(hand_landmarks).y * height
    diff = abs(top - bottom)

    return diff <= height*constants.FILTER_RATIO
    
    
def generate_uid():
    return str(uuid.uuid4())[:8]


def generate_frame_time():
    return str(int(time.time()))


def add_frame_to_buffer(frame):
    global flush_buffer, out_frame_count
    frame = frame.copy()

    # Adding frames to buffer
    frame_time = generate_frame_time()
    frame_buffer.append((frame_time, frame))

    # If the buffer is not queing out frames the contine
    if out_frame_count == -1:
        return

    # Keep track of when we should output out frames
    elif out_frame_count > 0:
        out_frame_count -= 1

    # When its time to output out frames flush the buffer
    else:
        flush_buffer = constants.Flush.OUT
        out_frame_count = -1
    