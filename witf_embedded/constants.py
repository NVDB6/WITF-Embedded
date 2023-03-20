from enum import Enum
import os
import cv2
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = os.path.join(PROJECT_ROOT, 'resources/input')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'resources/output')
DEVICE_CONFIG_FILE = os.path.join(PROJECT_ROOT, 'witf_embedded/device_config.json')

# OpenCV
DEFAULT_CODEC = cv2.VideoWriter_fourcc(*'avc1')
FPS = 30

# Hand Tracking
MIN_DETECTION_CONFIDENCE = 0.8
MIN_TRACKING_CONFIDENCE = 0.8
class ActionSegment(Enum):
    OUT = 0
    IN = 1
    UNDEF = 2
class Position(Enum):
    Left = 0
    RIGHT = 1