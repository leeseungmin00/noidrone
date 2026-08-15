# GUI.py
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np

import config
import state
import drone
import utils
import tracking
import approach
import rotate

class DroneMissionGUI:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1400x950")
        
        # 다크모드 색상 설정
        self.COLOR_BG = "#1e1e24"          
        self.COLOR_PANEL = "#2a2b36"       
        self.COLOR_TEXT = "#e3e3e6"        
        self.COLOR_ACCENT = "#4a90e2"      
        self.COLOR_GREEN = "#a3e635"       
        self.COLOR_PURPLE = "#c084fc"      
        self.COLOR_BLUE = "#38bdf8"        
        self.COLOR_RED = "#f87171"         
        
        self.window.configure(bg=self.COLOR_BG)
        
        # 내부 상태 및 동기화 변수
        self.gallery_images = []  
        self.last_photo_count = 0
        self.current_phase = "Standby"
        self.drone_thread = None       # 추가: 스레드 핸들 (아직 시작 안 함)
        
        # OpenCV waitKey와 동기화하기 위한 가상 키 버퍼 전역 변수 초기화
        state.gui_key_buffer = None
        
        # 노트북 키 입력 허용
        self.window.bind("<Key>", self.handle_key_press)
        
        # 레이아웃 분할 및 가중치 설정
        self.window.grid_rowconfigure(0, weight=1)  
        self.window.grid_rowconfigure(1, weight=0)  
        self.window.grid_columnconfigure(0, weight=1)
        
        # 상단 메인 영역 프레임
        self.top_main_frame = tk.Frame(window, bg=self.COLOR_BG)
        self.top_main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        self.top_main_frame.grid_columnconfigure(0, weight=3) 
        self.top_main_frame.grid_columnconfigure(1, weight=1) 
        self.top_main_frame.grid_rowconfigure(0, weight=1)
        
        # 좌측 영상 프레임
        self.left_frame = tk.Frame(self.top_main_frame, bg="#111115")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.video_label = tk.Label(self.left_frame, bg="#111115")
        self.video_label.pack(expand=True, fill=tk.BOTH)
        
        # 우측 대시보드 프레임
        self.right_frame = tk.Frame(self.top_main_frame, width=340, bg=self.COLOR_BG)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 15))
        self.right_frame.grid_propagate(False) 
        
        # 하단 갤러리 영역 프레임
        self.bottom_gallery_frame = tk.LabelFrame(window, text=" Captured Photos Gallery (Raw) ", padx=10, pady=5, 
                                                   font=("Helvetica", 10, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_GREEN, bd=1)
        self.bottom_gallery_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))
        
        self.gallery_canvas = tk.Canvas(self.bottom_gallery_frame, height=140, bg="#1a1b23", bd=0, highlightthickness=0)
        self.gallery_scrollbar = ttk.Scrollbar(self.bottom_gallery_frame, orient="horizontal", command=self.gallery_canvas.xview)
        
        self.gallery_inner_frame = tk.Frame(self.gallery_canvas, bg="#1a1b23")
        self.gallery_canvas.create_window((0, 0), window=self.gallery_inner_frame, anchor="nw")
        self.gallery_canvas.configure(xscrollcommand=self.gallery_scrollbar.set)
        
        self.gallery_canvas.pack(fill=tk.X, expand=True, side=tk.TOP)
        self.gallery_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.lbl_empty_gallery = tk.Label(self.gallery_inner_frame, text="Captured original images will be listed here...", 
                                          font=("Helvetica", 10, "italic"), bg="#1a1b23", fg="#6b7280", pady=50, padx=20)
        self.lbl_empty_gallery.pack()

        self.create_dashboard()
        
        # 변경: 시작 시 자동 연결 제거. START 버튼을 눌러야 연결 시작됨
        
        # GUI 자체 리프레시 루프 시작
        self.update_gui_loop()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_dashboard(self):
        title_label = tk.Label(self.right_frame, text="Tello Mission Dashboard", font=("Helvetica", 14, "bold"), bg=self.COLOR_BG, fg=self.COLOR_TEXT)
        title_label.pack(pady=5)

        # 추가: 미션 시작(연결) 버튼
        self.btn_start = tk.Button(self.right_frame, text="▶ START (Connect Drone)", font=("Helvetica", 12, "bold"),
                                   bg="#2563eb", fg="white", activebackground="#1d4ed8", bd=0, pady=10, cursor="hand2",
                                   command=self.start_mission)
        self.btn_start.pack(fill=tk.X, pady=(0, 8))

        # 비상정지 버튼 (언제든 눌러서 드론 정지)
        self.btn_emergency = tk.Button(self.right_frame, text="■ EMERGENCY STOP", font=("Helvetica", 12, "bold"),
                                       bg="#dc2626", fg="white", activebackground="#991b1b", bd=0, pady=10, cursor="hand2",
                                       command=self.trigger_emergency_stop)
        self.btn_emergency.pack(fill=tk.X, pady=(0, 8))
        
        # 타겟 설정을 위한 대시보드 버튼 세팅 영역
        self.target_ctrl_frame = tk.LabelFrame(self.right_frame, text=" Target Selection Control ", padx=10, pady=10, 
                                           font=("Helvetica", 10, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_ACCENT, bd=1)
        self.target_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.btn_next = tk.Button(self.target_ctrl_frame, text="Next Target (N)", font=("Helvetica", 10, "bold"),
                                  bg="#4b5563", fg="white", activebackground="#374151", bd=0, pady=6, cursor="hand2",
                                  command=self.trigger_n_key)
        self.btn_next.pack(fill=tk.X, pady=3)
        
        self.btn_select = tk.Button(self.target_ctrl_frame, text="Select Target (S)", font=("Helvetica", 10, "bold"),
                                    bg="#10b981", fg="white", activebackground="#059669", bd=0, pady=6, cursor="hand2",
                                    command=self.trigger_s_key)
        self.btn_select.pack(fill=tk.X, pady=3)
        
        # 실시간 상태 텔레메트리 보드
        info_frame = tk.LabelFrame(self.right_frame, text=" Telemetry Data ", padx=10, pady=10, 
                                   font=("Helvetica", 10, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_TEXT, bd=1)
        info_frame.pack(fill=tk.X, pady=5)
        
        labels_info = [
            ("Current Phase:", self.COLOR_PURPLE, "lbl_phase", "Standby"),
            ("Target ID Locked:", self.COLOR_RED, "lbl_id", "1"),
            ("Last Flight Order:", self.COLOR_BLUE, "lbl_order", "sss"),
            ("Saved Photos Count:", self.COLOR_GREEN, "lbl_photos", "0"),
            ("Rotation Sum:", self.COLOR_BLUE, "lbl_sum", "0")
        ]
        
        for idx, (txt, color, attr_name, default_val) in enumerate(labels_info):
            tk.Label(info_frame, text=txt, font=("Helvetica", 9), bg=self.COLOR_PANEL, fg="#9ca3af").grid(row=idx, column=0, sticky="w", pady=4)
            lbl = tk.Label(info_frame, text=default_val, font=("Helvetica", 10, "bold"), bg=self.COLOR_PANEL, fg=color)
            lbl.grid(row=idx, column=1, sticky="w", pady=4, padx=8)
            setattr(self, attr_name, lbl)
            
        # 시스템 로그 라벨 터미널
        tk.Label(self.right_frame, text="Mission Status Log:", font=("Helvetica", 9, "bold"), bg=self.COLOR_BG, fg="#9ca3af").pack(anchor="w", fill="x", pady=(5, 0))
        self.log_text = tk.Text(self.right_frame, height=18, width=35, font=("Courier", 9), 
                                 bg="#15151a", fg="#34d399", selectbackground="#3b4252", insertbackground="white",
                                 padx=8, pady=8, bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=2)

    def log(self, message):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)

    # 추가: START 버튼 핸들러 - 이때 비로소 연결 스레드 시작
    def start_mission(self):
        if self.drone_thread is not None and self.drone_thread.is_alive():
            self.log("Mission already running.")
            return
        self.btn_start.config(state=tk.DISABLED, bg="#374151")
        self.log("Starting mission...")
        self.drone_thread = threading.Thread(target=self.run_drone_sequence, daemon=True)
        self.drone_thread.start()

    # 비상정지 버튼 핸들러
    def trigger_emergency_stop(self):
        self.log(">>> EMERGENCY STOP ACTIVATED <<<")
        try:
            drone.emergency()
        except Exception as e:
            self.log(f"정지 명령 오류: {e}")
        self.current_phase = "EMERGENCY STOP"

    def run_drone_sequence(self):
        connected = False
        try:
            self.log("Initializing Drone Connection...")
            drone.connect()
            connected = True
            self.log("Drone Connected Successfully.")

            utils.make_folder()

            self.current_phase = "Target Setting"
            self.log("Phase [1]: Select Target Person. Press 'N' or 'S'.")

            tracking.make_target()

            self.btn_next.config(state=tk.DISABLED, bg="#374151")
            self.btn_select.config(state=tk.DISABLED, bg="#374151")

            self.current_phase = "Approach"
            self.log("Phase [2]: Target Locked. Initiating Approach Sequence...")
            approach.approach()

            self.current_phase = "Rotate"
            self.log("Phase [3]: Center Stabilized. Commencing 360 Rotation Photo Mission...")
            rotate.rotate_order()

            self.current_phase = "Completed"
            self.log("Mission Sequence Successfully Accomplished.")

        except Exception as e:
            self.log(f"Mission Exception: {str(e)}")
        finally:
            # 연결 실패 시엔 착륙/정지/저장을 시도하지 않고 조용히 종료
            if not connected:
                self.log("Drone connection failed. Press START to retry.")
                self.current_phase = "Connection Failed"
                # 재시도 가능하게 START 버튼 다시 활성화
                self.btn_start.config(state=tk.NORMAL, bg="#2563eb")
                return

            try:
                drone.stop()
                time.sleep(config.CONTROL_INTERVAL)
            except:
                pass
            self.log("Landing and Safe Shutdown Activated.")

            drone.land()
            drone.disconnect()
            if state.save_queue is not None:
                state.save_queue.join()

            utils.destroy_windows()

            self.current_phase = "Saving Decision"
            self.log("Waiting for user input: Save mission data?")

            self.window.after(0, self.ask_and_save)

    # 노트북 키보드 입력 핸들러
    def handle_key_press(self, event):
        if self.current_phase == "Target Setting":
            if event.char.lower() == 'n':
                self.trigger_n_key()
            elif event.char.lower() == 's':
                self.trigger_s_key()

    def trigger_n_key(self):
        if self.current_phase == "Target Setting":
            self.log("Action: Triggered [Next Target ID]")
            state.gui_key_buffer = ord('n')

    def trigger_s_key(self):
        if self.current_phase == "Target Setting":
            self.log("Action: Triggered [Target Selection Confirmed]")
            state.gui_key_buffer = ord('s')

    def add_image_to_gallery(self, raw_frame):
        if self.lbl_empty_gallery: 
            self.lbl_empty_gallery.destroy()
            self.lbl_empty_gallery = None

        h, w = raw_frame.shape[:2]
        thumb_h = 110
        aspect_ratio = w / h
        thumb_w = int(thumb_h * aspect_ratio)

        thumb_resized = cv2.resize(raw_frame, (thumb_w, thumb_h))
        thumb_rgb = cv2.cvtColor(thumb_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(thumb_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        
        self.gallery_images.append(img_tk)

        lbl_thumb = tk.Label(self.gallery_inner_frame, image=img_tk, bg="#2a2b36", bd=2, relief="groove")
        lbl_thumb.pack(side=tk.LEFT, padx=6, pady=5)
        
        self.gallery_inner_frame.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
        self.gallery_canvas.xview_moveto(1.0)

    def update_gui_loop(self):
        frame = None
        if state.display_frame is not None:
            frame = state.display_frame
        elif state.tello_video is not None:
            raw = state.tello_video.frame
            if raw is not None:
                raw = cv2.flip(raw, 1)
                frame = cv2.cvtColor(raw, cv2.COLOR_RGB2BGR)
        
        target_w = max(self.left_frame.winfo_width(), 100)
        target_h = max(self.left_frame.winfo_height(), 100)
        
        if frame is None:
            frame_disp = np.ones((target_h, target_w, 3), dtype="uint8") * 45  
            cv2.putText(frame_disp, "Press START to Connect Drone...", (int(target_w*0.22), int(target_h*0.5)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (180, 180, 185), 2)
        else:
            
            img_aspect = config.WIDTH / config.HEIGHT
            if target_w / target_h > img_aspect:
                new_h = target_h
                new_w = int(target_h * img_aspect)
            else:
                new_w = target_w
                new_h = int(target_w / img_aspect)
                
            frame_disp = cv2.resize(frame, (new_w, new_h))

            if state.photo_count > self.last_photo_count:
                self.last_photo_count = state.photo_count
                self.add_image_to_gallery(frame) 

        cv2image = cv2.cvtColor(frame_disp, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)
        
        self.lbl_phase.config(text=self.current_phase)
        self.lbl_id.config(text=str(state.target_id))
        self.lbl_order.config(text=str(state.last_order))
        self.lbl_photos.config(text=str(state.photo_count))
        self.lbl_sum.config(text=str(int(state.current_sum)))
        
        self.window.after(30, self.update_gui_loop)

    def on_closing(self):
        if state.tello is not None:
            try:
                drone.land()
                drone.disconnect()
            except:
                pass
        self.window.destroy()

    def ask_and_save(self):
        is_save = messagebox.askyesno(
            "Save Mission Data",
            "비행이 종료되었습니다. 촬영된 원본 사진 및 데이터를 저장하시겠습니까?"
        )

        if is_save:
            custom_name = simpledialog.askstring(
                "Input Folder Name",
                "저장할 결과물 폴더의 커스텀 이름을 입력하세요:\n(예: ObjectA_Front)",
                parent=self.window
            )

            if custom_name:
                custom_name = custom_name.strip().replace(" ", "_")
            else:
                custom_name = "default_session"

            self.log(f"Saving data with identifier: {custom_name}")

            try:
                utils.make_zip(custom_name)
                self.log("Mission files and ZIP archive successfully generated.")
                messagebox.showinfo("Success", f"성공적으로 백업되었습니다.\n식별자: {custom_name}")
            except Exception as zip_err:
                self.log(f"파일 저장 오류: {zip_err}")
        else:
            self.log("User discarded the session data. Temporary files will be deleted.")
            messagebox.showwarning("Discarded", "데이터 저장을 취소했습니다. 결과물이 생성되지 않습니다.")