# utils.py
from datetime import datetime
import os
import cv2
import shutil
import time

import state
import config

def make_folder():
    # 원본 사진들을 임시로 모아둘 날짜 폴더 생성
    state.save_folder = os.path.join(
        config.DRIVE_PATH,
        datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )
    os.makedirs(state.save_folder, exist_ok=True)
    
def destroy_windows():
    cv2.destroyAllWindows()

def make_zip(custom_name="default"):
    # 현재 날짜시간 포맷팅
    current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    
    # 코랩이 인식할 진짜 파일명
    pure_zip_name = f"photos_zip_{current_time}_{custom_name}"
    print(pure_zip_name)
    final_zip_path = os.path.join(config.DRIVE_PATH, pure_zip_name)
    
    # 압축 실행
    print('start')
    shutil.make_archive(final_zip_path, 'zip', state.save_folder)
    print("end")
    
    # 임시 폴더 삭제
    try:
        shutil.rmtree(state.save_folder)
    except Exception as e:
        print(f"임시 폴더 삭제 중 오류: {e}")