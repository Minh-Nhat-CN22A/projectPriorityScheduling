# animator.py
import customtkinter as ctk
import tkinter as tk

class RealtimeSimulator(ctk.CTkToplevel):
    def __init__(self, master, raw_data, gantt_data, aging_enabled=False, threshold=5):
        super().__init__(master)
        self.title("🎬 Mô phỏng Priority Scheduling - Chế độ Step-by-Step")
        self.geometry("950x800")
        self.attributes('-topmost', True) 
        
        # Ép giao diện sang chế độ Tối (Dark Mode) cho ngầu
        # ctk.set_appearance_mode("dark")

        self.raw_data = sorted(raw_data, key=lambda x: x['id'])
        self.gantt_data = gantt_data
        self.aging_enabled = aging_enabled
        self.threshold = threshold

        self.current_time = 0
        self.max_time = max([s['end'] for s in gantt_data]) if gantt_data else 0
        
        self.is_auto_playing = False
        self.after_id = None 

        # Bảng màu cho Biểu đồ Gantt
        self.colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
        self.color_map = {p['id']: self.colors[i % len(self.colors)] for i, p in enumerate(self.raw_data)}

        self.setup_ui()
        self.render_state()

    def setup_ui(self):
        # --- MÀU SẮC CHỦ ĐẠO ---
        BG_COLOR = "#111827"        # Nền chính cực tối
        CARD_COLOR = "#1f2937"      # Nền thẻ (nhạt hơn chút)
        TEXT_MAIN = "#f3f4f6"       # Trữ trắng xám
        TEXT_MUTED = "#9ca3af"      # Chữ xám mờ

        self.configure(fg_color=BG_COLOR)

        # ==========================================
        # 1. HEADER (Thanh trạng thái)
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))

        title_lbl = ctk.CTkLabel(header_frame, text="Mô phỏng Priority Scheduling (Aging)", font=("Arial", 24, "bold"), text_color=TEXT_MAIN)
        title_lbl.pack(side="left")

        stats_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        stats_frame.pack(side="right")

        self.lbl_time = ctk.CTkLabel(stats_frame, text="THỜI GIAN\n0s", font=("Arial", 14, "bold"), text_color="#fbbf24", justify="center")
        self.lbl_time.pack(side="left", padx=15)

        self.lbl_running = ctk.CTkLabel(stats_frame, text="ĐANG CHẠY\nNone", font=("Arial", 14, "bold"), text_color="#f87171", justify="center")
        self.lbl_running.pack(side="left", padx=15)

        self.lbl_done = ctk.CTkLabel(stats_frame, text=f"HOÀN THÀNH\n0/{len(self.raw_data)}", font=("Arial", 14, "bold"), text_color="#34d399", justify="center")
        self.lbl_done.pack(side="left", padx=15)

        # ==========================================
        # 2. KHU VỰC MAIN BOARD (Thẻ chứa nội dung)
        # ==========================================
        board = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        board.pack(fill="both", expand=True, padx=30, pady=10)

        # 2.1 LOGIC SUY LUẬN
        ctk.CTkLabel(board, text="LOGIC SUY LUẬN CỦA CPU", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 5))
        self.reason_lbl = ctk.CTkLabel(board, text="Đã khởi tạo. Nhấn 'Tiếp 1 bước' để bắt đầu.", font=("Arial", 15), text_color="#a7f3d0", justify="left")
        self.reason_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        # 2.2 BẢNG TIẾN TRÌNH (READY QUEUE TABLE)
        ctk.CTkLabel(board, text="Bảng Tiến trình (Ready Queue)", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 5))
        
        table_frame = ctk.CTkFrame(board, fg_color="transparent")
        table_frame.pack(fill="x", padx=20, pady=5)

        # Header Bảng
        headers = ["ID", "Đến", "Còn lại", "Priority", "Ưu tiên hiện tại", "Chờ"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(table_frame, text=text, font=("Arial", 14, "bold"), text_color=TEXT_MUTED, width=100, anchor="w").grid(row=0, column=col, padx=5, pady=5)

        # Các dòng dữ liệu
        self.table_cells = {}
        for row, p in enumerate(self.raw_data, start=1):
            pid = p['id']
            self.table_cells[pid] = {}
            
            # Khởi tạo các Label cho từng ô
            lbl_id = ctk.CTkLabel(table_frame, text=pid, font=("Arial", 14, "bold"), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_arr = ctk.CTkLabel(table_frame, text=f"{p['arrival_time']}s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_rem = ctk.CTkLabel(table_frame, text=f"{p['burst_time']}s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_pri = ctk.CTkLabel(table_frame, text=str(p['priority']), font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            
            # Ô Ưu tiên hiện tại có background để nổi bật
            frame_cur_pri = ctk.CTkFrame(table_frame, fg_color="transparent", corner_radius=5, width=100, height=30)
            frame_cur_pri.pack_propagate(False) # Giữ kích thước cố định
            lbl_cur_pri = ctk.CTkLabel(frame_cur_pri, text="-", font=("Arial", 14, "bold"), text_color=TEXT_MAIN)
            lbl_cur_pri.place(relx=0.1, rely=0.5, anchor="w")
            
            lbl_wait = ctk.CTkLabel(table_frame, text="0s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")

            # Đặt vào lưới (Grid)
            lbl_id.grid(row=row, column=0, padx=5, pady=8)
            lbl_arr.grid(row=row, column=1, padx=5, pady=8)
            lbl_rem.grid(row=row, column=2, padx=5, pady=8)
            lbl_pri.grid(row=row, column=3, padx=5, pady=8)
            frame_cur_pri.grid(row=row, column=4, padx=5, pady=8, sticky="w")
            lbl_wait.grid(row=row, column=5, padx=5, pady=8)

            # Lưu reference để update
            self.table_cells[pid] = {
                'rem': lbl_rem, 
                'cur_pri_frame': frame_cur_pri, 
                'cur_pri_text': lbl_cur_pri, 
                'wait': lbl_wait,
                'id': lbl_id
            }

        # 2.3 BIỂU ĐỒ GANTT (DÙNG CANVAS ĐỂ VẼ LIỀN MẠCH)
        ctk.CTkLabel(board, text="Biểu đồ Gantt", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.canvas_width = 850
        self.canvas_height = 60
        self.canvas = tk.Canvas(board, width=self.canvas_width, height=self.canvas_height, bg=CARD_COLOR, highlightthickness=0)
        self.canvas.pack(padx=20, pady=10)
        
        self.axis_canvas = tk.Canvas(board, width=self.canvas_width, height=30, bg=CARD_COLOR, highlightthickness=0)
        self.axis_canvas.pack(padx=20, pady=(0, 10))

        # ==========================================
        # 3. CONTROL PANEL (Thanh điều khiển)
        # ==========================================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=30, pady=15)

        # Nút bên trái (Reset & Lùi)
        self.btn_reset = ctk.CTkButton(ctrl_frame, text="🔄 Chạy lại", command=self.reset_sim, width=120, fg_color="#374151", hover_color="#4b5563")
        self.btn_reset.pack(side="left", padx=5)

        self.btn_back = ctk.CTkButton(ctrl_frame, text="⏮ Lùi 1 bước", command=self.step_back, width=120, fg_color="#4b5563", hover_color="#6b7280")
        self.btn_back.pack(side="left", padx=5)

        # Nút bên phải (Auto & Tiến)
        self.btn_next = ctk.CTkButton(ctrl_frame, text="Tiếp 1 bước ⏭", command=self.step_next, width=150, fg_color="#2563eb", hover_color="#1d4ed8", font=("Arial", 14, "bold"))
        self.btn_next.pack(side="right", padx=5)

        self.btn_auto = ctk.CTkButton(ctrl_frame, text="⏯ Tự động chạy", command=self.toggle_auto, width=150, fg_color="#059669", hover_color="#047857", font=("Arial", 14, "bold"))
        self.btn_auto.pack(side="right", padx=5)


    # ================= LOGIC ĐIỀU KHIỂN =================
    def step_next(self):
        if self.current_time < self.max_time:
            self.current_time += 1
            self.render_state()

    def step_back(self):
        if self.current_time > 0:
            self.current_time -= 1
            self.render_state()

    def toggle_auto(self):
        self.is_auto_playing = not self.is_auto_playing
        if self.is_auto_playing:
            self.btn_auto.configure(text="⏸ Tạm dừng", fg_color="#dc2626", hover_color="#b91c1c")
            self.btn_next.configure(state="disabled")
            self.btn_back.configure(state="disabled")
            self.auto_step()
        else:
            self.btn_auto.configure(text="⏯ Tự động chạy", fg_color="#059669", hover_color="#047857")
            self.btn_next.configure(state="normal")
            self.btn_back.configure(state="normal")
            if self.after_id:
                self.after_cancel(self.after_id)

    def auto_step(self):
        if self.is_auto_playing and self.current_time < self.max_time:
            self.current_time += 1
            self.render_state()
            self.after_id = self.after(800, self.auto_step) # Chạy 0.8s / bước cho mượt
        elif self.current_time >= self.max_time:
            self.toggle_auto() 

    def reset_sim(self):
        if self.after_id: self.after_cancel(self.after_id)
        self.is_auto_playing = False
        self.btn_auto.configure(text="⏯ Tự động chạy", fg_color="#059669")
        self.btn_next.configure(state="normal")
        self.btn_back.configure(state="normal")
        self.current_time = 0
        self.render_state()

    # ================= LOGIC VẼ GIAO DIỆN Ở GIÂY T =================
    def render_state(self):
        t = self.current_time
        
        # 1. Tìm tiến trình đang chạy & Tính số lượng hoàn thành
        running_p = None
        for s in self.gantt_data:
            if s['start'] <= t < s['end']:
                running_p = s['id']
                break

        completed_count = 0
        logic_msg = f"Thời điểm t = {t}s: "

        # 2. Cập nhật Bảng (Table)
        for p in self.raw_data:
            pid = p['id']
            cell = self.table_cells[pid]
            
            run_time = sum([min(s['end'], t) - max(s['start'], p['arrival_time']) 
                          for s in self.gantt_data if s['id'] == pid and s['start'] < t])
            rem_time = p['burst_time'] - run_time
            
            # Cập nhật Thời gian còn lại
            cell['rem'].configure(text=f"{rem_time}s" if rem_time > 0 else "0s")

            if t < p['arrival_time']:
                # Chưa đến
                cell['id'].configure(text_color="#4b5563")
                cell['cur_pri_text'].configure(text="-")
                cell['cur_pri_frame'].configure(fg_color="transparent")
                cell['wait'].configure(text="-")
            elif rem_time == 0:
                # Đã xong
                completed_count += 1
                cell['id'].configure(text_color="#9ca3af")
                cell['cur_pri_text'].configure(text="Xong")
                cell['cur_pri_frame'].configure(fg_color="transparent")
                cell['wait'].configure(text="-")
            else:
                # Đang chờ hoặc Đang chạy
                cell['id'].configure(text_color="#f3f4f6")
                wait_time = max(0, t - p['arrival_time'] - run_time)
                cell['wait'].configure(text=f"{wait_time}s")

                current_prio = p['priority']
                if self.aging_enabled:
                    boost = int(wait_time // self.threshold)
                    current_prio = max(1, p['priority'] - boost)

                cell['cur_pri_text'].configure(text=str(current_prio))
                
                # Highlight màu sắc
                if pid == running_p:
                    cell['cur_pri_frame'].configure(fg_color="#ef4444") # Đỏ - Đang chạy
                elif current_prio < p['priority']:
                    cell['cur_pri_frame'].configure(fg_color="#3b82f6") # Xanh - Đã được Aging
                else:
                    cell['cur_pri_frame'].configure(fg_color="#374151") # Xám - Bình thường

        # 3. Cập nhật Status Bar & Logic Text
        self.lbl_time.configure(text=f"THỜI GIAN\n{t}s")
        self.lbl_done.configure(text=f"HOÀN THÀNH\n{completed_count}/{len(self.raw_data)}")
        
        if t == self.max_time:
            self.lbl_running.configure(text="ĐANG CHẠY\nNone", text_color="#9ca3af")
            logic_msg = "🎉 HOÀN THÀNH MÔ PHỎNG: Tất cả tiến trình đã được lập lịch xong."
            self.reason_lbl.configure(text_color="#34d399")
        elif running_p:
            self.lbl_running.configure(text=f"ĐANG CHẠY\n{running_p}", text_color="#ef4444")
            logic_msg += f"CPU được cấp phát cho {running_p} (Trạng thái ưu tiên cao nhất)."
            self.reason_lbl.configure(text_color="#fbbf24")
        else:
            self.lbl_running.configure(text="ĐANG CHẠY\nNone", text_color="#9ca3af")
            logic_msg += "Hệ thống đang rảnh, chờ tiến trình mới."
            self.reason_lbl.configure(text_color="#a7f3d0")

        self.reason_lbl.configure(text=logic_msg)

        # 4. Vẽ Biểu đồ Gantt (Canvas)
        self.canvas.delete("all")
        self.axis_canvas.delete("all")
        
        if self.max_time > 0:
            px_per_sec = self.canvas_width / self.max_time
            
            # Vẽ các đoạn màu
            for s in self.gantt_data:
                if s['start'] < t:
                    draw_end = min(s['end'], t)
                    x0 = s['start'] * px_per_sec
                    x1 = draw_end * px_per_sec
                    color = self.color_map[s['id']]
                    self.canvas.create_rectangle(x0, 0, x1, self.canvas_height, fill=color, outline="white", width=1)
                    
                    # Căn giữa text trong khối
                    if (x1 - x0) > 20: 
                        self.canvas.create_text((x0 + x1)/2, self.canvas_height/2, text=s['id'], fill="white", font=("Arial", 12, "bold"))

            # Vẽ trục thời gian ở dưới
            for i in range(self.max_time + 1):
                x = i * px_per_sec
                # Vạch kẻ dọc nhẹ lên canvas chính
                self.canvas.create_line(x, 0, x, self.canvas_height, fill="#374151", dash=(2, 2))
                # Số giây ở canvas phụ
                self.axis_canvas.create_text(x, 15, text=str(i), fill="#9ca3af", font=("Arial", 10))