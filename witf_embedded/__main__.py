import json
import os
import time
import cv2
import constants
import argparse
from calibration import manual_calibrate
from classify import classify

### Args ###
parser = argparse.ArgumentParser()

parser.add_argument('--v', type=str, 
    help='[Optional] The name of the video to run the program on. If not provided, will capture from camera feed.')
parser.add_argument('--sf', type=str, help='[Optional] Save the selected frames to the given directory')
parser.add_argument('--c', action='store_false', help='[Optional] Go through calibration setup')

group = parser.add_mutually_exclusive_group()
group.add_argument('--d', action='store_true', help='[Optional] Turn debug mode on/off.')
group.add_argument('--sv', type=str, default='', help='[Optional] Save the resulting video at the given path.')

args = parser.parse_args()

# Parsed args
video_path = args.v and os.path.join(constants.INPUT_DIR, args.v)
save_frame_dir = args.sf and os.path.join(constants.OUTPUT_DIR, args.sf)
debug = bool(args.sv) or args.d
calibrated = args.c and os.path.exists(constants.DEVICE_CONFIG_FILE)
save_path = args.sv and os.path.join(constants.OUTPUT_DIR, args.sv)


### Capture ###
capture = cv2.VideoCapture(video_path or 0)


### Calibrate ###
if not calibrated:
    manual_calibrate(capture)

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
start = time.time()

if save_path:
    frames_per_second = constants.FPS
    codec = constants.DEFAULT_CODEC
    save_video = cv2.VideoWriter(save_path, codec, frames_per_second, (width, height))    

if save_frame_dir:
    os.makedirs(save_frame_dir)


### Main ###
while True:
    ret, frame = capture.read()

    if ret:
        counter +=1
        # Action Segmentation
        frame, selected_frame, selected_frame_id = classify(frame, width, height, top, bottom, debug=debug)
        if selected_frame is not None and save_frame_dir:
            cv2.imwrite(os.path.join(save_frame_dir, f'frame_{selected_frame_id}.png'), selected_frame)
        # Display the image
        cv2.imshow("Capture", frame)
        # Write frame to video
        if save_path:
            save_video.write(frame)
        # Debug output
        if debug:
            if counter % 50 == 0:
                print(f'Processed {counter} frames in {time.time()-start}s.')

        # Wait for user input
        key = cv2.waitKey(1)

        # If the user presses 'q', exit the loop
        if key == ord('q'):
            break
       
    else:
        break


### Cleanup ###
capture.release()
cv2.destroyAllWindows()

print(f'Processed {counter} frames in {time.time()-start}s.')

if save_path:
    save_video.release()
    print(f'Video saved to {save_path}')
