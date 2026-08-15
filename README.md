# NoiDrone

Python을 이용해 드론을 제어하고 사람의 사진을 찍어 3d 모델링 처리를 하는 프로젝트입니다.

## 프로젝트 소개

이 프로젝트는 드론의 비행을 제어하고 3d 모델링을 하기 위해 제작했습니다.

주요 기능
- 드론 비행 제어
- 객체 추적
- 객체 회전
- 사진 처리
- GUI를 통한 조작

## 파일 구조

| 파일         | 설명           |
| main.py      | 프로그램 실행   |
| GUI.py       | GUI 구성       |
| drone.py     | 드론 제어      |
| tracking.py  | 객체 추적      |
| photo.py     | 사진 관련 기능 |
| rotate.py    | 회전 제어      |
| state.py     | 드론 상태 관리 |
| approach.py  | 접근 관련 기능 |
| config.py    | 프로젝트 설정  |
| utils.py     | 공통 기능      |
| models/      | 모델 관련 파일 |

## 사용 기술
Python
Open cv2
YOLO pose
DJI tello
Tkinter
Pillow (PIL)
Meshroom API

## 실행 방법

필요 라이브러리 설치 후 main.py 실행

## 실행 결과

프로그램 실행 화면

<img width="1919" height="1028" alt="스크린샷 2026-08-15 182122" src="https://github.com/user-attachments/assets/02aedb92-3640-4ae8-bb00-536d1147cf14" />

드론 연결 시 드론 화면이 화면에 보입니다.
