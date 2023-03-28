import json
import multiprocess as multiprocessing
import os
import time
import cv2
import constants
import argparse
from capture import capture_frames, setup_capture, process_frame, process_frame_parallel
from calibration import manual_calibrate
from constants import LOGGER as logger

### Init Performance Variables ###
frame_counter = 0
classify_time = 0
show_time = 0


def setup_parser_and_parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--v', type=str, 
        help='[Optional] The name of the video to run the program on. If not provided, will capture from camera feed.')
    parser.add_argument('--sf', type=str, help='[Optional] Save the selected frames to the given directory')
    parser.add_argument('--c', action='store_false', help='[Optional] Go through calibration setup')
    parser.add_argument('--fl', action='store_true', help='[Optional] Inidicate if fridge is on left or right side of the frame')
    parser.add_argument('--pi', action='store_true', help='[Optional] Run script using config for raspberry pi')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--d', action='store_true', help='[Optional] Turn debug mode on/off.')
    group.add_argument('--sv', type=str, default='', help='[Optional] Save the resulting video at the given path.')

    return parser.parse_args()

def main_with_multiprocess(res_queue, cap_time, process_time, capture_process, process_process, save_in, save_out):
    global frame_counter
    started = False
    paused = False
    show_time = 0

    while True:
        key = cv2.waitKey(1)

         # Flush queue contents
        if key == ord('q'):
            capture_process.terminate()
            cap_time = cap_time.get()

            process_process.terminate()
            capture_process.join()
            logger.info(f'[TRACE]: Capture process joined...')


            # Must clear queues used by process frame or joion will block indefinitely
            process_time = process_time.get()
            
            while not res_queue.empty():
                frame = res_queue.get()
                frame_counter+=1
                cv2.imshow('frame', frame)
            
                if save_out:
                    save_out.write(frame)
                    save_in.write(frame)
                cv2.waitKey(1)

            process_process.join()
            logger.info(f'[TRACE]: Process process joined...')

            break

        if key == ord('p'):
            paused = not paused

        if paused:
            continue

        if res_queue.empty():
            continue

        if not started:
            start = time.perf_counter()
            started = True

        s1 = time.perf_counter()

        try:
            frame = res_queue.get(timeout=1)
        except Exception as e:
            logger.error(f'[NO FRAMES]: Res queue has no frames')
            continue

        frame_counter+=1
        cv2.imshow('frame', frame)

        if debug:
            if frame_counter % 50 == 0:
                logger.info(f'[PERFORMANCE][PROCESS TIME]: Current FPS {frame_counter/(time.perf_counter()-start)}fps')
                pass

        # Write frame to video
        if save_out:
            save_out.write(frame)
            save_in.write(frame)

        show_time += time.perf_counter() - s1
    
    return start, cap_time, process_time, show_time


if __name__ == '__main__':
    ### Args ###
    args = setup_parser_and_parse_args()

    ### Parsed args ###
    video_path = args.v and os.path.join(constants.INPUT_DIR, args.v)
    save_frame_dir = args.sf and os.path.join(constants.OUTPUT_DIR, args.sf)
    debug = bool(args.sv) or args.d
    fridge_left = args.fl
    calibrated = args.c and os.path.exists(constants.DEVICE_CONFIG_FILE)
    save_path_output = args.sv and os.path.join(constants.OUTPUT_DIR, args.sv)
    save_path_input = args.sv and os.path.join(constants.INPUT_DIR, args.sv)
    use_pi = args.pi   

    ### Setup Frame Capture Dir ###
    if save_frame_dir:
        try:
            os.makedirs(save_frame_dir)
        except FileExistsError as e:
            print(f"[TO FIX]: Delete the directory '{save_frame_dir}'")
            print(e)
            exit()

    ### Calibrate if necessary ###
    if not calibrated:
        capture = setup_capture(video_path)
        manual_calibrate(capture=capture)
        capture.release()

    ### Load calibration Config ###
    with open(constants.DEVICE_CONFIG_FILE, 'r') as file:
        # Load the JSON data from the file into a Python object
        config = json.load(file)
        width = config['width']
        height = config['height']
        top = config['boundary']['top']
        bottom = config['boundary']['bottom']
    # Close the file
    file.close()

    ### Configure save path ###
    save_video_input = None
    save_video_output = None
    if save_path_output:
        frames_per_second = constants.FPS
        codec = constants.DEFAULT_CODEC
        save_video_output = cv2.VideoWriter(save_path_output, codec, frames_per_second, (width, height))
        save_video_input = cv2.VideoWriter(save_path_input, codec, frames_per_second, (width, height))

    ## Main Loop ###
    multiprocessing.set_start_method('forkserver')
    cap_queue = multiprocessing.Queue(maxsize=constants.CAPTURE_BUFFER_SIZE)
    res_queue = multiprocessing.Queue()
    cap_time = multiprocessing.Queue()
    process_time = multiprocessing.Queue()

    capture_process = multiprocessing.Process(target=capture_frames, args=(video_path, cap_queue, cap_time))
    capture_process.start()

    process_process = multiprocessing.Process(target=process_frame_parallel, args=(cap_queue, res_queue, process_time, width, height, top, bottom, fridge_left, debug, save_frame_dir))
    process_process.start()

    start, cap_time, process_time, show_time = main_with_multiprocess(res_queue, cap_time, process_time, capture_process, process_process, save_video_input or None, save_video_output or None)

    finish = time.perf_counter()

    ### Cleanup ###


    cv2.destroyAllWindows()

    if save_path_output:
        save_video_output.release()
        #save_video_output.write(frame)
        logger.info(f'Video saved to {save_path_output}')

    ### Output Debug info ###
    logger.info(f'Processed {frame_counter} frames in {finish-start}s.')
    logger.info(f'Fps avg: {frame_counter/(finish-start):.2f}')
    logger.info(f'Capture time avg: {cap_time/frame_counter*1000:.2f}ms')
    logger.info(f'Process time avg: {process_time/frame_counter*1000:.2f}ms')
    logger.info(f'Show time avg: {show_time/frame_counter*1000:.2f}ms')
