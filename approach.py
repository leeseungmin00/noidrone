# approach.py
import cv2
import time

import config
import state

from tracking import make_order
from drone import tello_move


def approach():
    """
    타겟에게 접근한다.
    타겟이 화면 중앙에 일정 시간 유지되면 다음 단계로 넘어간다
    """

    while True:
        frame = state.tello_video.frame
        if frame is None:
            continue

        frame = cv2.flip(frame, 1)

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        order = make_order(
            frame=image,
            width=config.WIDTH,
            height=config.HEIGHT
        )

        tello_move(order)

        time.sleep(config.CONTROL_INTERVAL)

        # 접근 완료 판정

        if ((state.lost_time is None) and (order == "sss")):
            if (not state.sss_flag):
                state.sss_flag = True
                state.sss_time = time.time()
        else:
            state.sss_flag = False
            state.sss_time = None

        # 접근 완료 후 일정시간 뒤 회전 단계
        if (state.sss_flag and time.time() - state.sss_time > config.CENTER_TIME):
            break

        cv2.putText(image, order, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)

        if cv2.waitKey(1) == 27:
            break