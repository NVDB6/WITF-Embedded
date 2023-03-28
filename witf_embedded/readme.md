# Embedded software

The entry point for the prgram is `__main.py__`. 
  
## Running the program
You can run the program by running `$python witf_embedded.py`. Running the program without any command line arguments will start a live video feed.
If you have not gone through initial setup (i.e. if `device_config.json` does not exist) you will be prompted to draw the initial boundary line in a separate window called "Calibrate".
- To calibrate simply click where you want the boundary line to start, and click again for where you want it to end (after which you will see a green line projected ontop of the frame).
If you would like to drawn the line again simply click again to restart the process. 

After calibration is complete a file called `device_config.json` will be generated which contains some info about the boundary line as will as the camera height and width in px. 
> If you wish to manually calibrate upon starting the program, run the program with the `--c` option.
  
### CLI Reference 
`$python witf_embedded.py --help`

```
usage: witf_embedded [-h] [--v V] [--sf SF] [--c] [--d | --sv SV]


optional arguments:
  -h, --help  show this help message and exit
  --v V       [Optional] The name of the video to run the program on. If not provided, will capture from camera feed.
  --sf SF     [Optional] Save the selected frames to the given directory
  --c         [Optional] Go through calibration setup
  --d         [Optional] Turn debug mode on/off.
  --sv SV     [Optional] Save the resulting video at the given path.
  ```
  
### Example Usage
**1. Run the program using the live camera feed as input, calibrate the boundary, and save the resulting video to a file named `live_test.mp4`**
```
$python witf_embedded --c --sv live_test.mp4
```
  
**2. Run the program using the video `demo_1_short.mp4` as input, calibrate the boundary, save the resulting frames from frame selection in a directory called `demo_1_short` and save the video to a file named `demo_1_short_out.mp4`**
```
$python witf_embedded  --v demo_1_short.mp4 --c --sf demo_1_short --sv demo_1_short_out.mp4 
```
