import json
import os
import time
import cv2
import constants
import argparse
# from picamera2 import Picamera2 
# from picamera2.encoders import H264Encoder
# from picamera2.outputs import FfmpegOutput
from calibration import manual_calibrate
from classify import classify

### Args ###
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

args = parser.parse_args()

# Parsed args
video_path = args.v and os.path.join(constants.INPUT_DIR, args.v)
save_frame_dir = args.sf and os.path.join(constants.OUTPUT_DIR, args.sf)
debug = bool(args.sv) or args.d
fridge_left = args.fl
calibrated = args.c and os.path.exists(constants.DEVICE_CONFIG_FILE)
save_path = args.sv and os.path.join(constants.OUTPUT_DIR, args.sv)
use_pi = args.pi


### Capture ###
if use_pi:
    picam2 = Picamera2()
    config = picam2.create_still_configuration(lores={"size": (640, 480)}, buffer_count=5)
    picam2.configure(config)
    picam2.start()
else:
    capture = cv2.VideoCapture(video_path or 0)

### Calibrate ###
if not calibrated:
    if use_pi:
        manual_calibrate(pi_camera=picam2)
    else:
        manual_calibrate(capture=capture)

with open(constants.DEVICE_CONFIG_FILE, 'r') as file:
    # Load the JSON data from the file into a Python object
    config = json.load(file)
    width = config['width']
    height = config['height']
    top = config['boundary']['top']
    bottom = config['boundary']['bottom']
# Close the file
file.close()


### Init Variables ###
selected_frames = []
counter = 0
cap_time = 0
classify_time = 0
show_time = 0
start = time.time()

if save_path:
    frames_per_second = constants.FPS
    codec = constants.DEFAULT_CODEC
    save_video = cv2.VideoWriter(save_path, codec, frames_per_second, (width, height))    

if save_frame_dir:
    try:
        os.makedirs(save_frame_dir)
    except FileExistsError as e:
        print(f"[TO FIX]: Delete the directory '{save_frame_dir}'")
        print(e)
        exit()


### Main ###
while True:
    if use_pi:
        s = time.perf_counter()
        yuv420 = picam2.capture_array('lores')
        frame = cv2.cvtColor(yuv420, cv2.COLOR_YUV420p2BGR)
        ret = True
        f = time.perf_counter()
        cap_time += f-s 
    else:
        ret, frame = capture.read()

    if ret:
        counter +=1

        # Action Segmentation
        s = time.perf_counter()
        frame, selected_frames, selected_frame_ids = classify(frame, width, height, top, bottom, fridge_left, debug=debug)
        f = time.perf_counter()
        classify_time += f-s
        if selected_frames and save_frame_dir:
            for i, (selected_frame, selected_frame_id) in enumerate(zip(selected_frames, selected_frame_ids)):
                cv2.imwrite(os.path.join(save_frame_dir, f'frame_{selected_frame_id}_{i+1}.png'), selected_frame)

        # Display the image
        s = time.perf_counter()
        cv2.imshow("Capture", frame)
        f = time.perf_counter()
        show_time += f-s

        # Write frame to video
        if save_path:
            save_video.write(frame)

        # Debug output
        if debug:
            if counter % 50 == 0:
                print(f'Processed {counter} frames in {time.time()-start}s.')
                print(f'Framerate {counter/(time.time()-start)}fps')

        # Wait for user input
        key = cv2.waitKey(1)

        # If the user presses 'q', exit the loop
        if key == ord('q'):
            break
       
    else:
        break


### Cleanup ###
try:
    capture.release()
except:
    print()

cv2.destroyAllWindows()

if save_path:
    save_video.release()
    print(f'Video saved to {save_path}')


print(f'Processed {counter} frames in {time.time()-start}s.')
print(f'Fps avg: {counter/(time.time()-start)}')
print(f'Cap avg: {cap_time/counter}')
print(f'Classify avg: {classify_time/counter}')
print(f'Show avg: {show_time/counter}')