# drone.py
from djitellopy import Tello
import time
import config
import state


def connect():
    """드론 연결 및 영상 시작"""

    state.tello = Tello()

    state.tello.connect()
    time.sleep(config.CONTROL_INTERVAL)

    print(f"Battery : {state.tello.get_battery()}%")

    state.tello.streamon()
    state.tello.takeoff()

    time.sleep(2)

    state.tello_video = state.tello.get_frame_read()

def send_rc(lr, fb, ud, yaw):
    """RC 명령 전송"""

    # 추가: 비상정지 상태면 무조건 정지 명령만 전송 (버튼 눌리면 모든 움직임 차단)
    if state.emergency_stop:
        try:
            state.tello.send_rc_control(0, 0, 0, 0)
        except:
            pass
        return

    state.tello.send_rc_control(
        lr,
        fb,
        ud,
        yaw
    )

def stop():
    """호버"""
    send_rc(0, 0, 0, 0)

def emergency():
    """추가: 비상정지 - 플래그 세우고 즉시 정지 명령"""
    state.emergency_stop = True
    try:
        state.tello.send_rc_control(0, 0, 0, 0)
    except:
        pass

def land():
    """착륙"""
    try:
        state.tello.land()
    except:
        pass

def disconnect():
    """종료"""

    try:
        state.tello.streamoff()
    except Exception as e:
        print(f'착륙 오류 발생: {e}')

    try:
        state.tello.end()
    except Exception as e:
        print(f'정지 오류 발생: {e}')

def tello_move(order):
    """ 이동 """
    lr = 0
    fb = 0
    ud = 0

    if order[0] == 'l':
        state.target_yaw = -config.ROTATE_SPEED
    elif order[0] == 'r':
        state.target_yaw = config.ROTATE_SPEED
    else:
        state.target_yaw = 0

    # 부드럽게 회전 (가속/감속)
    state.last_yaw = int(state.last_yaw * (1 - config.ROTATE_ALPHA) + state.target_yaw * config.ROTATE_ALPHA)

    if order[1] == 'u':
        ud = config.MOVE_SPEED
    elif order[1] == 'd':
        ud = -config.MOVE_SPEED

    if order[2] == 'f':
        fb = config.MOVE_SPEED
    elif order[2] == 'b':
        fb = -config.MOVE_SPEED

    send_rc(lr, fb, ud, state.last_yaw)