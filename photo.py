# photo.py
import os
import threading
import cv2
from queue import Queue

import config
import state

state.save_queue = Queue()

def write_worker():
    while True:
        path, img = state.save_queue.get()
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, img)
        state.save_queue.task_done()

threading.Thread(target=write_worker, daemon=True).start()

# 사진 저장
def save_photo(frame, current_total_sum, phase):
    """ 사진 저장 """

    if current_total_sum - state.last_capture_sum < config.CAPTURE_INTERVAL:
        return

    state.last_capture_sum = current_total_sum

    filename = os.path.join(state.save_folder, f"img_{state.photo_count:03d}_{phase}.jpg")
    state.photo_count += 1

    state.save_queue.put((filename, frame.copy()))
