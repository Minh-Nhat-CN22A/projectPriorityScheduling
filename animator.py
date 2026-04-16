# animator.py
import customtkinter as ctk
import tkinter as tk

class RealtimeSimulator(ctk.CTkToplevel):
    def __init__(self, master, raw_data, gantt_data, aging_enabled=False, threshold=5):
        super().__init__(master)
        self.title("Priority Scheduling Simulation - Step-by-Step Mode")
        self.geometry("950x800")
        self.attributes('-topmost', True) 
        
        # Force Dark Mode for the UI
        # ctk.set_appearance_mode("dark")

        self.raw_data = sorted(raw_data, key=lambda x: x['id'])
        self.gantt_data = gantt_data
        self.aging_enabled = aging_enabled
        self.threshold = threshold

        self.current_time = 0
        self.max_time = max([s['end'] for s in gantt_data]) if gantt_data else 0
        
        self.is_auto_playing = False
        self.after_id = None 

        # Color palette for Gantt Chart
        self.colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
        self.color_map = {p['id']: self.colors[i % len(self.colors)] for i, p in enumerate(self.raw_data)}

        self.setup_ui()
        self.render_state()

    def setup_ui(self):
        # --- MAIN COLORS ---
        BG_COLOR = "#111827"        # Very dark main background
        CARD_COLOR = "#1f2937"      # Card background (slightly lighter)
        TEXT_MAIN = "#f3f4f6"       # Light gray/white text
        TEXT_MUTED = "#9ca3af"      # Muted gray text

        self.configure(fg_color=BG_COLOR)

        # ==========================================
        # 1. HEADER (Status Bar)
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))

        title_lbl = ctk.CTkLabel(header_frame, text="Priority Scheduling Simulation (Aging)", font=("Arial", 24, "bold"), text_color=TEXT_MAIN)
        title_lbl.pack(side="left")

        stats_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        stats_frame.pack(side="right")

        self.lbl_time = ctk.CTkLabel(stats_frame, text="TIME\n0s", font=("Arial", 14, "bold"), text_color="#fbbf24", justify="center")
        self.lbl_time.pack(side="left", padx=15)

        self.lbl_running = ctk.CTkLabel(stats_frame, text="RUNNING\nNone", font=("Arial", 14, "bold"), text_color="#f87171", justify="center")
        self.lbl_running.pack(side="left", padx=15)

        self.lbl_done = ctk.CTkLabel(stats_frame, text=f"COMPLETED\n0/{len(self.raw_data)}", font=("Arial", 14, "bold"), text_color="#34d399", justify="center")
        self.lbl_done.pack(side="left", padx=15)

        # ==========================================
        # 2. MAIN BOARD AREA (Content Card)
        # ==========================================
        board = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=15)
        board.pack(fill="both", expand=True, padx=30, pady=10)

        # 2.1 CPU REASONING LOGIC
        ctk.CTkLabel(board, text="CPU REASONING LOGIC", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 5))
        self.reason_lbl = ctk.CTkLabel(board, text="Initialized. Click 'Step Forward' to begin.", font=("Arial", 15), text_color="#a7f3d0", justify="left")
        self.reason_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        # 2.2 PROCESS TABLE (READY QUEUE)
        ctk.CTkLabel(board, text="Process Table (Ready Queue)", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10, 5))
        
        table_frame = ctk.CTkFrame(board, fg_color="transparent")
        table_frame.pack(fill="x", padx=20, pady=5)

        # Table Headers
        headers = ["ID", "Arrival", "Remaining", "Priority", "Current Priority", "Wait"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(table_frame, text=text, font=("Arial", 14, "bold"), text_color=TEXT_MUTED, width=100, anchor="w").grid(row=0, column=col, padx=5, pady=5)

        # Data Rows
        self.table_cells = {}
        for row, p in enumerate(self.raw_data, start=1):
            pid = p['id']
            self.table_cells[pid] = {}
            
            # Initialize Labels for each cell
            lbl_id = ctk.CTkLabel(table_frame, text=pid, font=("Arial", 14, "bold"), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_arr = ctk.CTkLabel(table_frame, text=f"{p['arrival_time']}s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_rem = ctk.CTkLabel(table_frame, text=f"{p['burst_time']}s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            lbl_pri = ctk.CTkLabel(table_frame, text=str(p['priority']), font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")
            
            # Current Priority cell has a background to stand out
            frame_cur_pri = ctk.CTkFrame(table_frame, fg_color="transparent", corner_radius=5, width=100, height=30)
            frame_cur_pri.pack_propagate(False) # Keep fixed size
            lbl_cur_pri = ctk.CTkLabel(frame_cur_pri, text="-", font=("Arial", 14, "bold"), text_color=TEXT_MAIN)
            lbl_cur_pri.place(relx=0.1, rely=0.5, anchor="w")
            
            lbl_wait = ctk.CTkLabel(table_frame, text="0s", font=("Arial", 14), text_color=TEXT_MAIN, width=100, anchor="w")

            # Place into Grid
            lbl_id.grid(row=row, column=0, padx=5, pady=8)
            lbl_arr.grid(row=row, column=1, padx=5, pady=8)
            lbl_rem.grid(row=row, column=2, padx=5, pady=8)
            lbl_pri.grid(row=row, column=3, padx=5, pady=8)
            frame_cur_pri.grid(row=row, column=4, padx=5, pady=8, sticky="w")
            lbl_wait.grid(row=row, column=5, padx=5, pady=8)

            # Store references to update later
            self.table_cells[pid] = {
                'rem': lbl_rem, 
                'cur_pri_frame': frame_cur_pri, 
                'cur_pri_text': lbl_cur_pri, 
                'wait': lbl_wait,
                'id': lbl_id
            }

        # 2.3 GANTT CHART (USING CANVAS FOR CONTINUOUS DRAWING)
        ctk.CTkLabel(board, text="Gantt Chart", font=("Arial", 18, "bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.canvas_width = 850
        self.canvas_height = 60
        self.canvas = tk.Canvas(board, width=self.canvas_width, height=self.canvas_height, bg=CARD_COLOR, highlightthickness=0)
        self.canvas.pack(padx=20, pady=10)
        
        self.axis_canvas = tk.Canvas(board, width=self.canvas_width, height=30, bg=CARD_COLOR, highlightthickness=0)
        self.axis_canvas.pack(padx=20, pady=(0, 10))

        # ==========================================
        # 3. CONTROL PANEL
        # ==========================================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=30, pady=15)

        # Left Buttons (Reset & Step Back)
        self.btn_reset = ctk.CTkButton(ctrl_frame, text="🔄 Reset", command=self.reset_sim, width=120, fg_color="#374151", hover_color="#4b5563")
        self.btn_reset.pack(side="left", padx=5)

        self.btn_back = ctk.CTkButton(ctrl_frame, text="⏮ Step Back", command=self.step_back, width=120, fg_color="#4b5563", hover_color="#6b7280")
        self.btn_back.pack(side="left", padx=5)

        # Right Buttons (Auto Play & Step Forward)
        self.btn_next = ctk.CTkButton(ctrl_frame, text="Step Forward ⏭", command=self.step_next, width=150, fg_color="#2563eb", hover_color="#1d4ed8", font=("Arial", 14, "bold"))
        self.btn_next.pack(side="right", padx=5)

        self.btn_auto = ctk.CTkButton(ctrl_frame, text="⏯ Auto Play", command=self.toggle_auto, width=150, fg_color="#059669", hover_color="#047857", font=("Arial", 14, "bold"))
        self.btn_auto.pack(side="right", padx=5)


    # ================= CONTROL LOGIC =================
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
            self.btn_auto.configure(text="⏸ Pause", fg_color="#dc2626", hover_color="#b91c1c")
            self.btn_next.configure(state="disabled")
            self.btn_back.configure(state="disabled")
            self.auto_step()
        else:
            self.btn_auto.configure(text="⏯ Auto Play", fg_color="#059669", hover_color="#047857")
            self.btn_next.configure(state="normal")
            self.btn_back.configure(state="normal")
            if self.after_id:
                self.after_cancel(self.after_id)

    def auto_step(self):
        if self.is_auto_playing and self.current_time < self.max_time:
            self.current_time += 1
            self.render_state()
            self.after_id = self.after(800, self.auto_step) # Run 0.8s / step for smoothness
        elif self.current_time >= self.max_time:
            self.toggle_auto() 

    def reset_sim(self):
        if self.after_id: self.after_cancel(self.after_id)
        self.is_auto_playing = False
        self.btn_auto.configure(text="⏯ Auto Play", fg_color="#059669")
        self.btn_next.configure(state="normal")
        self.btn_back.configure(state="normal")
        self.current_time = 0
        self.render_state()

    # ================= UI RENDERING LOGIC AT TIME T =================
    def render_state(self):
        t = self.current_time
        
        # 1. Find the running process & Calculate completed count
        running_p = None
        for s in self.gantt_data:
            if s['start'] <= t < s['end']:
                running_p = s['id']
                break

        completed_count = 0
        logic_msg = f"Time t = {t}s: "

        # 2. Update Table
        for p in self.raw_data:
            pid = p['id']
            cell = self.table_cells[pid]
            
            run_time = sum([min(s['end'], t) - max(s['start'], p['arrival_time']) 
                          for s in self.gantt_data if s['id'] == pid and s['start'] < t])
            rem_time = p['burst_time'] - run_time
            
            # Update Remaining Time
            cell['rem'].configure(text=f"{rem_time}s" if rem_time > 0 else "0s")

            if t < p['arrival_time']:
                # Not yet arrived
                cell['id'].configure(text_color="#4b5563")
                cell['cur_pri_text'].configure(text="-")
                cell['cur_pri_frame'].configure(fg_color="transparent")
                cell['wait'].configure(text="-")
            elif rem_time == 0:
                # Completed
                completed_count += 1
                cell['id'].configure(text_color="#9ca3af")
                cell['cur_pri_text'].configure(text="Done")
                cell['cur_pri_frame'].configure(fg_color="transparent")
                cell['wait'].configure(text="-")
            else:
                # Waiting or Running
                cell['id'].configure(text_color="#f3f4f6")
                wait_time = max(0, t - p['arrival_time'] - run_time)
                cell['wait'].configure(text=f"{wait_time}s")

                current_prio = p['priority']
                if self.aging_enabled:
                    boost = int(wait_time // self.threshold)
                    current_prio = max(1, p['priority'] - boost)

                cell['cur_pri_text'].configure(text=str(current_prio))
                
                # Color Highlighting
                if pid == running_p:
                    cell['cur_pri_frame'].configure(fg_color="#ef4444") # Red - Running
                elif current_prio < p['priority']:
                    cell['cur_pri_frame'].configure(fg_color="#3b82f6") # Blue - Aged (Priority Boosted)
                else:
                    cell['cur_pri_frame'].configure(fg_color="#374151") # Gray - Normal

        # 3. Update Status Bar & Logic Text
        self.lbl_time.configure(text=f"TIME\n{t}s")
        self.lbl_done.configure(text=f"COMPLETED\n{completed_count}/{len(self.raw_data)}")
        
        if t == self.max_time:
            self.lbl_running.configure(text="RUNNING\nNone", text_color="#9ca3af")
            logic_msg = "🎉 SIMULATION COMPLETE: All processes have been scheduled."
            self.reason_lbl.configure(text_color="#34d399")
        elif running_p:
            self.lbl_running.configure(text=f"RUNNING\n{running_p}", text_color="#ef4444")
            logic_msg += f"CPU allocated to {running_p} (Highest priority state)."
            self.reason_lbl.configure(text_color="#fbbf24")
        else:
            self.lbl_running.configure(text="RUNNING\nNone", text_color="#9ca3af")
            logic_msg += "System is idle, waiting for new processes."
            self.reason_lbl.configure(text_color="#a7f3d0")

        self.reason_lbl.configure(text=logic_msg)

        # 4. Draw Gantt Chart (Canvas)
        self.canvas.delete("all")
        self.axis_canvas.delete("all")
        
        if self.max_time > 0:
            px_per_sec = self.canvas_width / self.max_time
            
            # Draw color blocks
            for s in self.gantt_data:
                if s['start'] < t:
                    draw_end = min(s['end'], t)
                    x0 = s['start'] * px_per_sec
                    x1 = draw_end * px_per_sec
                    color = self.color_map[s['id']]
                    self.canvas.create_rectangle(x0, 0, x1, self.canvas_height, fill=color, outline="white", width=1)
                    
                    # Center text inside the block
                    if (x1 - x0) > 20: 
                        self.canvas.create_text((x0 + x1)/2, self.canvas_height/2, text=s['id'], fill="white", font=("Arial", 12, "bold"))

            # Draw time axis below
            for i in range(self.max_time + 1):
                x = i * px_per_sec
                # Light vertical line on the main canvas
                self.canvas.create_line(x, 0, x, self.canvas_height, fill="#374151", dash=(2, 2))
                # Seconds text on the secondary canvas
                self.axis_canvas.create_text(x, 15, text=str(i), fill="#9ca3af", font=("Arial", 10))