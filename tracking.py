# tracking.py
import cv2
import time

import config
import state



# 타겟 정의
def make_target():
    # 타겟 설정
    state.gui_key_buffer = None

    while True:
        frame = state.tello_video.frame
        if frame is None: continue
        frame = cv2.flip(frame, 1)

        result = config.MODEL.track(frame, classes=[0], persist=True, verbose=False)
        image=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        r = result[0]
        if r.boxes is not None:
            for i in range(len(r.boxes)):
                if r.boxes[i].id is None: continue
                
                x1, y1, x2, y2 = r.boxes[i].xyxy[0]
                curr_id = int(r.boxes[i].id[0])
                
                # 선택된 타겟은 빨간색, 나머지는 초록색
                if curr_id == state.target_id:
                    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
                    cv2.putText(image, f"TARGET {curr_id}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
                else:
                    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)

        state.display_frame = image
        state.tello.send_rc_control(0, 0, 0, 0)
        key = cv2.waitKey(1)

        if getattr(state, 'gui_key_buffer', None) is not None:
            key = state.gui_key_buffer
            state.gui_key_buffer = None

        if key == ord('n'):
            if r.boxes is not None and len(r.boxes) > 0:
                
                id_list = [int(b.id[0]) for b in r.boxes if b.id is not None]
                if id_list:
                    if state.target_id in id_list:
                        idx = (id_list.index(state.target_id) + 1) % len(id_list)
                        state.target_id = id_list[idx]
                    else:
                        state.target_id = id_list[0]
        
        if key == ord('s'):
            break

# 타겟 재정의
def retarget_by_position(r, width):

    if state.last_seen_x is None or state.last_seen_y is None:
        return False

    # 놓친 직후엔 retarget 안 함 (탐색으로 방향부터 돌게)
    if state.lost_time is not None:
        elapsed = time.time() - state.lost_time
        if elapsed < config.RETARGET_DELAY:
            return False
        if elapsed > config.RETARGET_TIMEOUT:
            return False

    if r.boxes is None or len(r.boxes) == 0 or r.keypoints is None:
        return False

    for box in r.boxes:
        if box.id is not None and int(box.id[0]) == state.target_id:
            return False

    best_id=None
    best_dist=None

    for i, box in enumerate(r.boxes):
        if box.id is None:
            continue

        kp=r.keypoints.xy[i]
        kx=int(kp[1][0]+kp[2][0])//2
        ky=int(kp[5][1]+kp[6][1]+kp[11][1]+kp[12][1])//4

        dist=((kx-state.last_seen_x)**2+(ky-state.last_seen_y)**2)**0.5

        if best_dist is None or dist<best_dist:
            best_dist=dist
            best_id=int(box.id[0])

    # 거리 기준 좁힘 (0.5 → 0.15)
    if best_id is not None and best_dist < width*config.RETARGET_DIST:
        state.target_id=best_id
        state.lost_time=None
        return True

    return False

# 이동 명령 생성
def make_order(frame, width, height):

    image=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result=config.MODEL.track(image, classes=[0], persist=True, verbose=False)

    

    r=result[0]

    if r.boxes is not None and len(r.boxes) > 0 and r.keypoints is not None:
        for i, box in enumerate(r.boxes):

            if box.id is not None and int(box.id[0]) == state.target_id:
                kp=r.keypoints.xy[i]
                left_shoulderx=min(kp[5][0], kp[6][0])
                right_shoulderx=max(kp[5][0], kp[6][0])

                kx, ky=int(kp[1][0]+kp[2][0])//2, int(kp[5][1]+kp[6][1]+kp[11][1]+kp[12][1])//4

                x1,y1,x2,y2 = box.xyxy[0]

                # 짧을 때 보정
                if (x2-x1<width*config.SHORT_WIDTH):
                    x1 = max(x1-(x2-x1)*0.25, 0)
                    x2 = min(x2+(x2-x1)*0.25, width)

                # 팔 보정
                if (x1+config.ARM_SHOULDER_DIST<left_shoulderx):
                    x1=max(0,min(left_shoulderx, kx)-config.ARM_SHOULDER_DIST//2)
                if (right_shoulderx<x2-config.ARM_SHOULDER_DIST):
                    x2=min(width,max(right_shoulderx, kx)+config.ARM_SHOULDER_DIST//2)

                if config.DEBUG:
                    cv2.rectangle(# 가로선
                        frame,
                        (0, int(height*config.UP_LINE)),
                        (int(width), int(height*config.DOWN_LINE)),
                        (0,0,0),
                        2
                    )

                    cv2.rectangle(# 세로선
                        frame,
                        (int(width*config.LEFT_LINE), 0),
                        (int(width*config.RIGHT_LINE), int(height)),
                        (0,0,0),
                        2
                    )
                    
                    cv2.rectangle(# 박스
                        frame,
                        (int(x1), int(y1)),
                        (int(x2), int(y2)),
                        (0,255,0),
                        2
                    )

                    cv2.circle(frame, (kx, ky), 10, (0, 0, 255), -1)
                    cv2.circle(frame, (int(kp[5][0]), int(kp[5][1])), 10, (0, 255, 0), -1)
                    cv2.circle(frame, (int(kp[6][0]), int(kp[6][1])), 10, (0, 255, 0), -1)
                    cv2.circle(frame, (int(kp[9][0]), int(kp[9][1])), 10, (255, 0, 0), -1)
                    cv2.circle(frame, (int(kp[10][0]), int(kp[10][1])), 10, (255, 0, 0), -1)


                    cv2.rectangle(# 박스
                        frame,
                        (int(x1), int(y1)),
                        (int(x2), int(y2)),
                        (255,255,0),
                        2
                    )
                
                state.display_frame = frame
                order=''
                # 좌우 판단
                if (kx<width*config.LEFT_LINE):
                    order+='r'
                elif (width*config.RIGHT_LINE<kx):
                    order+='l'
                else:
                    order+='s'

                # 상하 판단
                if (ky<height*config.UP_LINE):
                    order+='u'
                elif (height*config.DOWN_LINE<ky):
                    order+='d'
                else:
                    order+='s'

                # 거리 판단
                body_width=x2-x1
                body_height=y2-y1
                body_rate=body_height*body_width/(width*height)

                if (body_rate<config.SMALL_RATE):
                    order+='f'
                elif (config.BIG_RATE<body_rate):
                    order+='b'
                else:
                    order+='s'

                #정상 인식, 놓침기록 초기화,상태 저장
                state.lost_time=None
                state.last_order=order
                state.last_seen_x=kx
                state.last_seen_y=ky
                return order
    
    state.display_frame = frame
    # 타겟 못 찾았을 때
    if state.lost_time is None: # 방금 막 놓쳤으면 놓친 시각 기록
        state.lost_time=time.time()

    
    if retarget_by_position(r, width):
        return state.last_order if state.last_order is not None else 'sss'
    
    if state.last_seen_x is not None:
        if state.last_seen_x < width * 0.5:
            return 'rss'
        else:
            return 'lss'
    return 'sss' #한 번도 본 적 없으면 정지