import json
import os
import sys
import cv2
from typing import Tuple
import constants

def manual_calibrate(capture=None, pi_camera=None) -> Tuple[Tuple[int,int], Tuple[int, int]]:
    p1 = (0, 0)
    p2 = (0, 0)
    start_point = (0, 0)
    end_point = (0, 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) if capture else pi_camera.camera_config['lores']['size'][0]
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) if capture else pi_camera.camera_config['lores']['size'][1]

    line_drawn = False

    ret, frame = capture.read() if capture else (True, cv2.cvtColor(pi_camera.capture_array('lores'), cv2.COLOR_YUV420p2RGB))

    if not ret:
        sys.exit("Could not get frame for calibration")
    
    orig = frame.copy()

    # Create a named window to display the image
    cv2.namedWindow("Calibrate")

    # Set a mouse callback function to the window
    def draw_line(event, x, y, flags, param):
        nonlocal p1, p2, line_drawn, frame, start_point, end_point

        if event == cv2.EVENT_LBUTTONDOWN:
            if line_drawn:
                frame = orig.copy()
                line_drawn = False
            if p1 == (0, 0):
                p1 = (x, y)
            elif p2 == (0, 0):
                p2 = (x, y)

        if p1 != (0, 0) and p2 != (0, 0):
            # Calculate the slope of the line, None if slope is vertical
            delta_y = (p2[1]-p1[1])
            delta_x = (p2[0]-p1[0])
            slope = delta_y/delta_x if delta_x != 0 else None
            # Calculate the x-int of the line
            x_intercept = (frame.shape[0] - p1[1])/slope + p1[0] if slope != None else p1[0]
            # Calculate the start and end point of the line
            start_point = ((int(-p1[1]/slope if slope != None else 0) + p1[0], 0))
            end_point = ((int(x_intercept), frame.shape[0]))
            # Draw the line
            cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
            line_drawn = True

            print(f"Start: {start_point}\n End: {end_point}")
            # Reset the points
            p1 = (0, 0)
            p2 = (0, 0)

    cv2.setMouseCallback("Calibrate", draw_line)

    while True:
        # Display the image
        cv2.imshow("Calibrate", frame)

        # Wait for user input
        key = cv2.waitKey(1)

        # If the user presses 'q', exit the loop
        if key == ord('q'):
            break

        # If user presses 'r', reload the frame
        if key == ord('r'):
            ret, frame = capture.read() if capture else (True, cv2.cvtColor(pi_camera.capture_array('lores'), cv2.COLOR_YUV420p2RGB))
            orig = frame.copy()
            if not ret:
                sys.exit("Could not get frame for calibration")

        # If the user presses 's', exit the loop and save points to json file
        if key == ord('s') and line_drawn:
            filename = constants.DEVICE_CONFIG_FILE

            if not os.path.exists(filename):
                open(filename, 'w').close()

            with open(filename, 'r') as jsonFile:
                try:
                    data = json.load(jsonFile)
                except:
                    data = {}

            data['boundary'] = {
                'top': {
                    'x': start_point[0],
                    'y': start_point[1]
                },
                'bottom': {
                    'x': end_point[0],
                    'y': end_point[1]
                }
            }
            data['width'] = width
            data['height'] = height

            with open(filename, "w") as jsonFile:
                json.dump(data, jsonFile)

            print("Points saved to JSON file.")
            break

    # Release the window
    cv2.destroyWindow('Calibrate')

if __name__ == '__main__':
    manual_calibrate()