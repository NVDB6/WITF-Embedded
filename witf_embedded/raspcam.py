import time

from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

record_time = 10
resolution_x = 1920
resolution_y = 1080
save_video_file_name = 'test.mp4'

picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={'size': (resolution_x, resolution_y)})
picam2.configure(video_config)

encoder = H264Encoder(10000000)
output = FfmpegOutput(f'../resources/input/{save_video_file_name}')
picam2.start_preview(Preview.QTGL)
picam2.start_recording(encoder, output)
time.sleep(record_time)
picam2.stop_recording()

