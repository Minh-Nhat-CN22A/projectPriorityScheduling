# main.py - File chạy chính
import customtkinter as ctk
from algorithms import *
from ui_components import create_input_row
from visualizer import draw_gantt_chart, draw_comparison_chart
from animator import RealtimeSimulator  # Import thêm module hoạt hình

# --- KHỞI TẠO ỨNG DỤNG ---
app = ctk.CTk()
app.title("Simulator Lập lịch Priority")
app.geometry("1100x850") 

# --- BIẾN TOÀN CỤC ---
entries = []
last_simulation_data = None  # Biến lưu trữ dữ liệu tính toán để truyền cho Popup Mô phỏng

# --- CÁC HÀM XỬ LÝ SỰ KIỆN ---
def delete_row(frame_to_remove):
    """Xóa hàng nhập liệu khỏi danh sách và giao diện"""
    for entry in entries:
        if entry['frame'] == frame_to_remove:
            entry['frame'].destroy()
            entries.remove(entry)
            break

def add_process():
    """Thêm một dòng nhập liệu mới"""
    idx = len(entries) + 1
    new_entry = create_input_row(input_scroll, idx, delete_row)
    entries.append(new_entry)

def open_animation():
    """Hàm mở cửa sổ popup mô phỏng Real-time"""
    global last_simulation_data
    if last_simulation_data is None:
        compare_label.configure(text="⚠️ Hãy bấm CHẠY trước để có dữ liệu mô phỏng!", text_color="orange")
        return
    
    # Khởi tạo Cửa sổ Mô phỏng với dữ liệu vừa tính
    RealtimeSimulator(
        app, 
        last_simulation_data['raw_data'], 
        last_simulation_data['gantt'], 
        last_simulation_data['aging'], 
        last_simulation_data['threshold']
    )

def run():
    """Hàm lõi chạy thuật toán, vẽ biểu đồ và phân tích kết quả"""
    global last_simulation_data
    
    try:
        raw_data = []
        for i, e in enumerate(entries):
            if not e['arrival'].get() or not e['burst'].get() or not e['priority'].get():
                raise ValueError(f"Tiến trình P{i+1} còn thiếu dữ liệu!")
                
            raw_data.append({
                "id": f"P{i+1}",
                "arrival_time": int(e['arrival'].get()),
                "burst_time": int(e['burst'].get()),
                "priority": int(e['priority'].get())
            })
        
        if not raw_data:
            compare_label.configure(text="Vui lòng thêm ít nhất một tiến trình!", text_color="orange")
            return

        # --- LẤY THÔNG SỐ AGING TỪ GIAO DIỆN ---
        is_aging_enabled = aging_var.get()
        try:
            aging_threshold = int(threshold_var.get())
            if aging_threshold <= 0: raise ValueError
        except ValueError:
            raise ValueError("Ngưỡng Aging phải là số nguyên lớn hơn 0!")

        # 1. Chạy Priority theo menu chọn
        mode = algo_var.get()
        if mode == "Priority (Non-Preemptive)":
            res_p, gantt = priority_non_preemptive(raw_data, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        else:
            res_p, gantt = priority_preemptive(raw_data, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        
        # 2. Chạy ngầm FCFS để có mốc so sánh
        res_f = fcfs_algorithm(raw_data)
        
        # --- LƯU TRỮ LẠI DỮ LIỆU CHO MÔ PHỎNG REAL-TIME ---
        last_simulation_data = {
            'raw_data': raw_data,
            'gantt': gantt,
            'aging': is_aging_enabled,
            'threshold': aging_threshold
        }
        
        # 3. Vẽ biểu đồ Gantt (Vào Tab 1)
        draw_gantt_chart(tab_gantt, raw_data, gantt, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        
        # 4. Tính toán các chỉ số
        p_wt, p_tat = calculate_metrics(res_p)
        f_wt, f_tat = calculate_metrics(res_f)
        
        # 5. Vẽ biểu đồ cột so sánh (Vào Tab 2)
        draw_comparison_chart(chart_report_frame, p_wt, p_tat, f_wt, f_tat, mode)

        # 6. Logic tính toán phần trăm và Đưa ra kết luận (AI-like)
        diff_wt = round(((f_wt - p_wt) / f_wt) * 100, 1) if f_wt != 0 else 0
        diff_tat = round(((f_tat - p_tat) / f_tat) * 100, 1) if f_tat != 0 else 0

        # Phân tích điều kiện (Efficiency Gap Analysis)
        if diff_wt > 0 and diff_tat > 0:
            insight = "🌟 TỐI ƯU TOÀN DIỆN: Thuật toán Priority hiện tại vượt trội hơn FCFS ở cả hai chỉ số. Phù hợp cho hệ thống cần xử lý công việc quan trọng nhanh chóng mà không làm suy giảm năng suất tổng thể."
            final_color = "#2ECC71"
        elif diff_wt > 0 and diff_tat <= 0:
            insight = "⚖️ ĐÁNH ĐỔI (TRADE-OFF): Priority giúp hệ thống phản hồi nhanh hơn (giảm WT) nhưng làm giảm năng suất tổng thể (TAT bị kéo dài do ngắt quãng hoặc có tiến trình dài). Phù hợp cho hệ thống tương tác trực tiếp cần độ nhạy cao."
            final_color = "#F1C40F"
        elif diff_wt < 0:
            insight = "⚠️ KÉM HIỆU QUẢ: Priority đang hoạt động kém hơn FCFS. Nguyên nhân thường do 'Đảo ngược ưu tiên' (Tiến trình dài có ưu tiên cao cản trở tiến trình ngắn). Cần xem xét lại cách gán mức ưu tiên hoặc bật tính năng Aging."
            final_color = "#E74C3C"
        else:
            insight = "Tương đương nhau."
            final_color = "white"

        comparison_text = (
            f"📊 ĐỘ LỆCH HIỆU NĂNG (EFFICIENCY GAP):\n"
            f"{'—'*50}\n"
            f"👉 Hiệu quả WT : {'Tốt hơn' if diff_wt >= 0 else 'Kém hơn'} FCFS {abs(diff_wt)}%\n"
            f"👉 Hiệu quả TAT: {'Tốt hơn' if diff_tat >= 0 else 'Kém hơn'} FCFS {abs(diff_tat)}%\n\n"
            f"💡 KẾT LUẬN:\n{insight}"
        )
        
        compare_label.configure(text=comparison_text, text_color=final_color)
        
    except ValueError as ve:
        compare_label.configure(text=f"⚠️ {ve}", text_color="orange")
    except Exception as e:
        compare_label.configure(text=f"❌ Lỗi hệ thống: {e}", text_color="red")


# ==========================================
# --- LAYOUT GIAO DIỆN (UI COMPONENTS) ---
# ==========================================

# 1. Khu vực Nhập liệu
input_scroll = ctk.CTkScrollableFrame(app, width=500, height=250, label_text="Dữ liệu đầu vào")
input_scroll.pack(pady=10)

# 2. Khay Nút bấm Điều khiển
ctrl_frame = ctk.CTkFrame(app)
ctrl_frame.pack(pady=10)

ctk.CTkButton(ctrl_frame, text="+ Thêm P", command=add_process, width=100).grid(row=0, column=0, padx=5, pady=5)

algo_var = ctk.StringVar(value="Priority (Preemptive)")
ctk.CTkOptionMenu(ctrl_frame, variable=algo_var, values=["Priority (Non-Preemptive)", "Priority (Preemptive)"]).grid(row=0, column=1, padx=5, pady=5)

ctk.CTkButton(ctrl_frame, text="CHẠY", command=run, fg_color="green", width=100).grid(row=0, column=2, padx=5, pady=5)

# Nút Gọi Mô Phỏng Real-time
ctk.CTkButton(ctrl_frame, text="🎬 Mô phỏng Real-time", command=open_animation, fg_color="#3498db", width=150).grid(row=0, column=3, padx=10, pady=5)

# 3. Khu vực Cài đặt Aging
aging_frame = ctk.CTkFrame(app, fg_color="transparent")
aging_frame.pack(pady=5)

aging_var = ctk.BooleanVar(value=False)
aging_checkbox = ctk.CTkCheckBox(aging_frame, text="Bật Aging (Chống đói tài nguyên)", variable=aging_var, text_color="#F1C40F")
aging_checkbox.pack(side="left", padx=10)

ctk.CTkLabel(aging_frame, text="Ngưỡng (s):").pack(side="left")
threshold_var = ctk.StringVar(value="5")
threshold_entry = ctk.CTkEntry(aging_frame, textvariable=threshold_var, width=50)
threshold_entry.pack(side="left", padx=5)

# 4. Khu vực Hiển thị Kết quả (Sử dụng Tabview)
tabview = ctk.CTkTabview(app, width=1050, height=450)
tabview.pack(pady=10, fill="both", expand=True, padx=20)

tab_gantt = tabview.add("Biểu đồ Gantt & Timeline")
tab_report = tabview.add("Báo cáo Hiệu năng (Comparison Report)")

# Bố cục bên trong Tab "Báo cáo Hiệu năng"
report_text_frame = ctk.CTkFrame(tab_report, width=400, fg_color="transparent")
report_text_frame.pack(side="left", fill="both", expand=False, padx=20, pady=20)

compare_label = ctk.CTkLabel(report_text_frame, text="Bấm CHẠY để xem phân tích so sánh", 
                             font=("Arial", 14, "bold"), justify="left", wraplength=350)
compare_label.pack(pady=20, anchor="w")

chart_report_frame = ctk.CTkFrame(tab_report, fg_color="white")
chart_report_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Chạy vòng lặp ứng dụng
app.mainloop()