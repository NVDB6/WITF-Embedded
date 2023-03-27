import json
import multiprocess as multiprocessing
import os
import time
import cv2
import constants
import argparse
from capture import capture_frames, setup_capture, process_frame
from calibration import manual_calibrate
from constants import LOGGER as logger

### Init Performance Variables ###
frame_counter = 0
cap_time = 0
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
    if save_path_output:
        frames_per_second = constants.FPS
        codec = constants.DEFAULT_CODEC
        save_video_output = cv2.VideoWriter(save_path_output, codec, frames_per_second, (width, height))
        save_video_input = cv2.VideoWriter(save_path_input, codec, frames_per_second, (width, height))

    ## Main Loop ###
    multiprocessing.set_start_method('spawn')
    #pool = multiprocessing.Pool(processes=4)
    mp_queue = multiprocessing.Queue(maxsize=constants.FRAME_BUFFER_SIZE)
    cap_time = multiprocessing.Queue()

    capture_process = multiprocessing.Process(target=capture_frames, args=(video_path, mp_queue, cap_time))
    capture_process.start()
    time.sleep(1)

    def callback(frame):
        cv2.imshow('frame', frame)

    started = False
    while True:
        if mp_queue.empty():
            #logger.warning(f'[NO FRAMES]: Queue is empty')
            continue

        if not started:
            start = time.perf_counter()
            started = True

        frame = mp_queue.get(timeout=1)
        frame_counter+=1
        # pool.apply_async(process_frame, args=(frame, width, height, top, bottom, fridge_left, debug, save_frame_dir), callback=lambda x: callback(x[0]))

        processed_frame, t = process_frame(frame, width, height, top, bottom, fridge_left, debug=debug, save_frame_dir=save_frame_dir)
        classify_time+=t
        cv2.imshow('frame', processed_frame)

        if debug:
            if frame_counter % 50 == 0:
                logger.debug(f'[PROCESS TIME]: Current FPS {frame_counter/(time.perf_counter()-start)}fps')
                pass

        # Write frame to video
        if save_path_output:
            save_video_output.write(processed_frame)
            save_video_input.write(frame)

        # Flush queue contents
        if cv2.waitKey(1) == ord('q'):
            capture_process.terminate()

            while not mp_queue.empty():
                frame = mp_queue.get(timeout=1)
                frame_counter+=1
                processed_frame, t = process_frame(frame, width, height, top, bottom, fridge_left, debug=debug, save_frame_dir=save_frame_dir)
                classify_time+=t
                cv2.imshow('frame', processed_frame)

                if save_path_output:
                    save_video_output.write(processed_frame)
                    save_video_input.write(frame)

            cap_time = cap_time.get()
            break

    finish = time.perf_counter()

    ### Cleanup ###
    logger.info('Terminating capture process...')
    capture_process.join()

    cv2.destroyAllWindows()

    if save_path_output:
        save_video_output.release()
        save_video_output.write(frame)
        logger.info(f'Video saved to {save_path_output}')

    ### Output Debug info ###
    logger.info(f'Processed {frame_counter} frames in {finish-start}s.')
    logger.info(f'Fps avg: {frame_counter/(finish-start)}')
    logger.info(f'Capture time avg: {cap_time/frame_counter}')
    logger.info(f'Classify time avg: {classify_time/frame_counter}')
    logger.info(f'Show time avg: {show_time/frame_counter}')

### Main ###
# while True:
#     s1 = time.perf_counter()
#     if use_pi:
#         yuv420 = picam2.capture_array('lores')
#         frame = cv2.cvtColor(yuv420, cv2.COLOR_YUV420p2BGR)
#         ret = True
#     else:
#         s = time.perf_counter()
#         ret, frame = capture.read()
#         logger.info(f'[CAPTURE TIME]: {time.perf_counter() - s}')

#     if ret:
#         counter +=1

#         if (video_path):
#             current_time_sec = capture.get(cv2.CAP_PROP_POS_MSEC)/1000
#             logger.debug(f'Proccessing frame at {current_time_sec:.2f} sec')

#         # Action Segmentation
#         s = time.perf_counter()
#         frame, selected_frames, selected_frame_ids = classify(frame, width, height, top, bottom, fridge_left, debug=debug)
#         f = time.perf_counter()
#         classify_time += f-s
#         logger.info(f'[CLASSIFY TIME]: {time.perf_counter() - s}')


#         #print('p1', f-s)
#         s = time.perf_counter()
#         if selected_frames and save_frame_dir:
#             for i, (selected_frame, selected_frame_id) in enumerate(zip(selected_frames, selected_frame_ids)):
#                 path = os.path.join(save_frame_dir, f'frame_{selected_frame_id}_{i+1}.png')
#                 cv2.imwrite(path, selected_frame)
#                 with lock:
#                     paths.append(path)
        
#         # Write frame to video
#         if save_path:
#             save_video.write(frame)
            
#         # API
#         if len(paths) >= 10:
#             paths_to_send = paths.copy()  # Create a copy of the paths list to send on another thread
#             paths = []  # Clear the paths list
#             #threading.Thread(target=send_batch, args=(paths_to_send,)).start()
#         logger.debug(f'[SAVE + API TIME]: {time.perf_counter() - s}')

#         # Debug output
#         if debug:
#             if counter % 50 == 0:
#                 # logger.info(f'Processed {counter} frames in {time.time()-start}s.')
#                 # logger.info(f'Framerate {counter/(time.time()-start)}fps')
#                 pass

#         s = time.perf_counter()
#         # Display the image. If the user presses 'q', exit the loop
#         cv2.imshow("Capture", frame)
#         # Wait for user input + show the image
#         if cv2.waitKey(1) == ord('q'):
#             break
#         f = time.perf_counter()
#         show_time += f-s
#         logger.debug(f'[SHOW TIME]: {time.perf_counter() - s}')

#         logger.debug(f'[TOTAL ITERATION TIME]: {time.perf_counter() - s1}')
       
#     else:
#         break
# finish = time.perf_counter()