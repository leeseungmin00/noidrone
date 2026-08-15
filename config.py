# config.py
from ultralytics import YOLO

# Drone

MOVE_SPEED = 20 # 이동 속도
ROTATE_SPEED = 30 # 회전 속도
CONTROL_INTERVAL = 0.05 # 명령 간 간격


# Camera
# 카메라 비율
WIDTH = 960
HEIGHT = 720

# 드론과 타겟의 좌우 판단
RIGHT_LINE = 0.65
LEFT_LINE = 0.35

# 드론과 타겟의 상하 판단
UP_LINE = 0.4
DOWN_LINE = 0.6

# 드론과 타겟의 거리 판단
SMALL_RATE = 0.3
BIG_RATE = 0.5

SHORT_WIDTH = 0.13 # 옆을 본다를 확인하는 기준
ARM_SHOULDER_DIST = 200 # 팔을 벌렸다의 기준

CENTER_TIME = 6 # 접근 후 회전 대기 시간
 
# Rotate
TARGET_SUM = 3000 # 360도 회전 값
MIX_RATIO = 0.1 # 어깨->골반 이동 비율

# 부드러운 방향 조절
ROTATE_ALPHA = 0.3 
BASE_YAW = -15
GAIN = -0.05

# 회전 시 이동 제한
MAX_ROTATE = 40
MIN_LR = 5
MAX_UD = 20
SLOW_MOVE = 15

ROTATE_WEIGHT = 20 # 좌우 오차 가중치

# Retarget
RETARGET_DIST = 0.15
RETARGET_DELAY = 1.0
RETARGET_TIMEOUT = 4.0

# Capture
CAPTURE_INTERVAL = 60

# FILE
DRIVE_PATH = r"G:\내 드라이브\photos_zip"

# MODEL
MODEL = YOLO("models/yolov8n-pose.pt")

#
DEBUG = True