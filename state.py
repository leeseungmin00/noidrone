# state.py
# drone
tello = None # 연결된 텔로
tello_video = None # 텔로 화면 연결
last_yaw = 0
target_yaw = 0

# tracking
lost_time = None
last_order = None
target_id = None

display_frame = None

last_seen_x = None
last_seen_y = None

sss_time = None
sss_flag = False

# capture
photo_count = 0
last_capture_sum = 0
save_folder = None
current_sum = 0

gui_key_buffer = None

save_queue = None

emergency_stop = False