# rotate.py
import cv2
import time
import tracking

import config
import state
import photo
import drone

# 회전 명령 루프
def rotate_order():
    shoulder_sum = 0
    hip_sum = 0
    mix_sum = 0 

    MIX_ZONE = config.TARGET_SUM * config.MIX_RATIO

    while True:
        frame = state.tello_video.frame
        if frame is None:
            continue

        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        state.display_frame = image

        ratio = 0.0

        if shoulder_sum < (config.TARGET_SUM - MIX_ZONE):
            phase = "shoulder"
        elif mix_sum < MIX_ZONE:
            phase = "mix"
            ratio = mix_sum / MIX_ZONE 
        elif hip_sum < config.TARGET_SUM:
            phase = "hip"
        else:
            break

        # 드론 제어 명령 전송 및 yaw 값 획득
        yaw = tello_person_rotate(frame=image, width=config.WIDTH, height=config.HEIGHT, pivot=phase, ratio=ratio)

        # 각 페이즈에 맞게 누적 수치 증가 
        if phase == "shoulder":
            shoulder_sum += abs(yaw)
        elif phase == "mix":
            mix_sum += abs(yaw)
        elif phase == "hip":
            hip_sum += abs(yaw)

        # 전체 누적 명령량을 기반 사진 촬영
        current_total_sum = shoulder_sum + mix_sum + hip_sum
        state.current_sum = current_total_sum
        photo.save_photo(frame, current_total_sum, phase)

        time.sleep(config.CONTROL_INTERVAL)


        cv2.putText(image, f"Phase: {phase} (Ratio: {ratio:.2f})", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        if cv2.waitKey(1) == 27:
            break

# 사람 중심 회전
def tello_person_rotate(frame, width, height, pivot, ratio=0.0):
    save_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = config.MODEL.track(save_image, classes=[0], persist=True, verbose=False)
    r = result[0]

    # 사람/키포인트 없으면 멈춤
    if r.boxes is None or len(r.boxes) == 0 or r.keypoints is None:
        drone.stop()
        return 0

    for i, box in enumerate(r.boxes):
        if box.id is None or int(box.id[0]) != state.target_id:
            continue

        kp = r.keypoints.xy[i]

        # 각 기준점 계산
        # 어깨중점
        sx = (kp[5][0] + kp[6][0]) / 2
        shoulder_y = (kp[5][1] + kp[6][1]) / 2
        # 코 (머리)
        nose_y = kp[0][1]
        # 골반중점
        hx = (kp[11][0] + kp[12][0]) / 2
        hip_y = (kp[11][1] + kp[12][1]) / 2
        # 무릎중점
        knee_y = (kp[13][1] + kp[14][1]) / 2

        # 어깨 기준: 머리(코)와 어깨의 중간 지점
        sy = (nose_y + shoulder_y) / 2
        # 골반 기준: 골반과 무릎의 중간 지점 (= 허벅지 중앙)
        hy = (knee_y)

        # 페이즈에 따른 최종 피벗 계산 (선형 보간 Lerp 통합)
        if pivot == "shoulder":
            px, py = sx, sy
        elif pivot == "hip":
            px, py = hx, hy
        elif pivot == "mix":
            px = sx * (1 - ratio) + hx * ratio
            py = sy * (1 - ratio) + hy * ratio

        # mix 페이즈든 아니든 언제나 화면에 타겟 포인트를 그려줌
        cv2.circle(frame, (int(px), int(py)), 10, (0, 0, 255), -1)

        x1, y1, x2, y2 = box.xyxy[0]
        body_width = x2 - x1
        body_height = y2 - y1
        body_rate = body_width * body_height / (width * height)

        # 연속 회전 로직 적용
        error_x = px - width / 3
        yaw = int(config.BASE_YAW + error_x * config.GAIN)
        yaw = max(-config.MAX_ROTATE, min(config.MAX_ROTATE, yaw))

        # 고도 보정
        error_y = py - height / 2
        ud = int(-error_y * 0.1)
        ud = max(-config.MAX_UD, min(config.MAX_UD, ud))

        # 거리 보정 (mix 페이즈에서도 정상 작동하도록 복구)
        if body_rate < config.SMALL_RATE:
            fb = config.SLOW_MOVE
        elif body_rate > config.BIG_RATE:
            fb = -config.SLOW_MOVE
        else:
            fb = 0

        # 옆이동 속도 조절
        center_error = abs(error_x) / (width / 2)
        lr = int(config.ROTATE_WEIGHT * (1 - center_error*0.5))
        lr = min(lr, -config.MIN_LR)

        lr = 25

        drone.send_rc(lr, fb, ud, yaw)
        return yaw

    drone.stop()
    tracking.retarget_by_position(r, width)
    return 0
