from enum import Enum
import logging
import os
import cv2
from pathlib import Path

# Debug
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('embedded.log')

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

LOGGER = logger

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = os.path.join(PROJECT_ROOT, 'resources/input')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'resources/output')
DEVICE_CONFIG_FILE = os.path.join(PROJECT_ROOT, 'witf_embedded/device_config.json')

# OpenCV
DEFAULT_CODEC = cv2.VideoWriter_fourcc(*'avc1')
FPS = 30

# Hand Tracking
MIN_DETECTION_CONFIDENCE = 0.60
MIN_TRACKING_CONFIDENCE = 0.60
STATIC_IMAGE_MODE = True
MAX_NUM_HANDS = 2
DOWNSCALE_FACTOR = 1
FILTER_RATIO = 1/6
# Actions
class ActionSegment(Enum):
    OUT = 0
    IN = 1
    UNDEF = 2

class Position(Enum):
    Left = 0
    RIGHT = 1

# Frame Selection
FRAME_BUFFER_SIZE = 3

class Flush(Enum):
    IN = 0
    OUT = 1

# Capture
WIDTH = 1920
HEIGHT = 1280
CAPTURE_BUFFER_SIZE = 10