import os
import sys
import threading
import constants
import cv2
import time
import signal

from api import send_batch
from classify import classify
from constants import LOGGER as logger

lock = threading.Lock()
paths = {}

def setup_capture(video_path):
    capture = cv2.VideoCapture(video_path or 0)
    print(capture.set(cv2.CAP_PROP_FRAME_WIDTH, constants.WIDTH))
    print(capture.set(cv2.CAP_PROP_FRAME_HEIGHT, constants.HEIGHT))

    logger.debug('All properties:')
    logger.debug('----------------')
    for prop in dir(cv2):
        if prop.startswith('CAP_PROP_'):
            logger.debug(f'{prop}: {capture.get(getattr(cv2, prop))}')
    logger.debug('----------------')

    # Sleep to give time for camera to initialize
    time.sleep(1)

    return capture


def capture_frames(video_path, queue, res):
    # from constants import LOGGER as logger
    # import time
    # import signal
    # from capture import setup_capture 

    cap_time = 0
    cap = setup_capture(video_path=video_path)
    logger.info('[TRACE]: Capturing frames...')
    exit_flag = False

    def signal_handler(signal, frame):
        global exit_flag
        cap.release()
        nonlocal cap_time
        res.put(cap_time)
        exit_flag = True
        logger.info('[TRACE]: Terminating capture process...')
        sys.exit()

    signal.signal(signal.SIGTERM, signal_handler)
    
    time.sleep(1)
    logger.debug('[TRACE]: Done sleeping...')

    while not exit_flag:
        s = time.perf_counter()
        ret, frame = cap.read()
        t = time.perf_counter() - s
        if not ret:
            logger.fatal('[CAPTURE ERROR]: Could not read frame')
            break
        if t > 0.04:
            logger.warning(f'[PERFORMANCE[[HIGH PROCESS TIME]: Capture took {t:.4f}s')
        cap_time += time.perf_counter() - s
            
        queue.put(frame)



def process_frame_parallel(frame_queue, res_queue, process_time, width, height, top, bottom, fridge_left, debug=False, save_frame_dir=None):
    global paths

    proc_time = 0
    exit_flag = False

    def update_paths(selected_frames, selected_frame_ids, save_frame_dir):
        uid = None
        for i, (selected_frame, selected_frame_id) in enumerate(zip(selected_frames, selected_frame_ids)):
            path = os.path.join(save_frame_dir, f'frame_{selected_frame_id}_{i+1}.png')
            cv2.imwrite(path, selected_frame)
            with lock:
                uid = selected_frame_id.split('_')[1]
                # If key already in dict, then these frames must be the corresponding out frames
                if uid in paths:
                    paths[uid].append(path)
                else: # theres are new in frames
                    paths[uid] = [path]

        assert uid is not None
        # if the new frames added are the out frames, then send both the in and out frames to the server
        if len(paths[uid]) >= 2*constants.FRAME_BUFFER_SIZE:
            paths_to_send = paths[uid]  # Create a copy of the paths list to send on another thread
            del paths[uid]   # Clear the paths for this action id
            logger.info(f'[API][UID: ${uid}] Sending Frames...')
            threading.Thread(target=send_batch, args=(paths_to_send,)).start()

    def signal_handler(signal, fr):
        nonlocal proc_time, frame_queue
        global exit_flag
        logger.info('[TRACE]: Terminating process process...')

        exit_flag = True
        while not frame_queue.empty():
            s = time.perf_counter()
            # Action Segmentation
            frame, selected_frames, selected_frame_ids = classify(frame_queue.get(), width, height, top, bottom, fridge_left, debug=debug)
            # Gather frames and send to API
            if selected_frames and save_frame_dir:
                update_paths(selected_frames, selected_frame_ids, save_frame_dir)
            res_queue.put(frame)
            f = time.perf_counter()
            t = f - s
            proc_time += t

        process_time.put(proc_time)
        logger.info('[TRACE]: Terminating process process DONE')
        sys.exit()

    signal.signal(signal.SIGTERM, signal_handler)

    while not exit_flag:
        if frame_queue.empty():
            continue
        s = time.perf_counter()
        # Action Segmentation
        frame, selected_frames, selected_frame_ids = classify(frame_queue.get(), width, height, top, bottom, fridge_left, debug=debug)
        # Gather frames and send to API
        if selected_frames and save_frame_dir:
            update_paths(selected_frames, selected_frame_ids, save_frame_dir)
        
        res_queue.put(frame)

        f = time.perf_counter()
        t = f - s
        proc_time += t
        if t > 0.08: logger.warning(f'[PERFORMANCE][HIGH PROCESS TIME]: Process frames took {t}')



def process_frame(frame, width, height, top, bottom, fridge_left, debug=False, save_frame_dir=None):
    global paths

    def update_paths(selected_frames, selected_frame_ids, save_frame_dir):
        uid = None
        for i, (selected_frame, selected_frame_id) in enumerate(zip(selected_frames, selected_frame_ids)):
            path = os.path.join(save_frame_dir, f'frame_{selected_frame_id}_{i+1}.png')
            cv2.imwrite(path, selected_frame)
            with lock:
                uid = selected_frame_id.split('_')[1]
                # If key already in dict, then these frames must be the corresponding out frames
                if uid in paths:
                    paths[uid].append(path)
                else: # theres are new in frames
                    paths[uid] = [path]

        assert uid is not None
        # if the new frames added are the out frames, then send both the in and out frames to the server
        if len(paths[uid]) >= 2*constants.FRAME_BUFFER_SIZE:
            paths_to_send = paths[uid]  # Create a copy of the paths list to send on another thread
            del paths[uid]   # Clear the paths for this action id
            logger.info(f'[API][UID: ${uid}] Sending Frames...')
            threading.Thread(target=send_batch, args=(paths_to_send,)).start()

    s = time.perf_counter()

    # Action Segmentation
    frame, selected_frames, selected_frame_ids = classify(frame, width, height, top, bottom, fridge_left, debug=debug)
    
    # Gather frames and send to API
    if selected_frames and save_frame_dir:
        update_paths(selected_frames, selected_frame_ids, save_frame_dir)

    f = time.perf_counter()
    t = f - s
    logger.debug(f'[PERFORMANCE][PROCESS TIME]: Process frames took {t}')
    #if t > 0.05: logger.warning(f'[PERFORMANCE][HIGH PROCESS TIME]: Process frames took {t}')

    return frame, t