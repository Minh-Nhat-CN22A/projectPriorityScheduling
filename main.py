# main.py - File chạy chính
import customtkinter as ctk
from algorithms import *
from ui_components import create_input_row
from visualizer import draw_gantt_chart

app = ctk.CTk()
app.title("Simulator Lập lịch Priority")
app.geometry("1100x800")

entries = []

def delete_row(frame_to_remove):
    """Xóa hàng nhập liệu khỏi danh sách và giao diện"""
    for entry in entries:
        if entry['frame'] == frame_to_remove:
            entry['frame'].destroy()
            entries.remove(entry)
            break

def add_process():
    idx = len(entries) + 1
    new_entry = create_input_row(input_scroll, idx, delete_row)
    entries.append(new_entry)

def run():
    # 0. Khởi tạo giá trị mặc định để Pylance không "than phiền"
    txt_color = "white" 
    
    try:
        raw_data = []
        for i, e in enumerate(entries):
            # Kiểm tra xem các ô có trống không trước khi int()
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

        # 1. Chạy Priority theo menu chọn
        mode = algo_var.get()
        if mode == "Priority (Non-Preemptive)":
            res_p, gantt = priority_non_preemptive(raw_data)
        else:
            res_p, gantt = priority_preemptive(raw_data)
        
        # 2. Chạy ngầm FCFS để so sánh
        res_f = fcfs_algorithm(raw_data)
        
        # 3. Vẽ biểu đồ Gantt
        draw_gantt_chart(chart_frame, raw_data, gantt)
        
        # 4. Tính toán các chỉ số trung bình
        p_wt, p_tat = calculate_metrics(res_p)
        f_wt, f_tat = calculate_metrics(res_f)
        
        # 5. Tính toán hiệu quả (%)
        diff_wt = round(((f_wt - p_wt) / f_wt) * 100, 1) if f_wt != 0 else 0
        diff_tat = round(((f_tat - p_tat) / f_tat) * 100, 1) if f_tat != 0 else 0

        # Logic chọn Icon và nội dung cho WT
        if diff_wt >= 0:
            status_wt = f"✅ Tốt hơn FCFS {diff_wt}%"
        else:
            status_wt = f"❌ Kém hơn FCFS {abs(diff_wt)}%"

        # Logic chọn Icon và nội dung cho TAT
        if diff_tat >= 0:
            status_tat = f"✅ Tốt hơn FCFS {diff_tat}%"
        else:
            status_tat = f"❌ Kém hơn FCFS {abs(diff_tat)}%"

        # Quyết định màu tổng thể của Bảng (Màu vàng nếu kết quả hỗn hợp)
        if (diff_wt >= 0 and diff_tat >= 0):
            final_color = "#2ECC71" # Xanh toàn diện
        elif (diff_wt < 0 and diff_tat < 0):
            final_color = "#E74C3C" # Đỏ toàn diện
        else:
            final_color = "#F1C40F" # VÀNG: Kết quả hỗn hợp (Cảnh báo thầy lưu ý)

        comparison_text = (
            f"📊 KẾT QUẢ SO SÁNH CHI TIẾT:\n"
            f"{'—'*45}\n"
            f"🔹 {mode}:\n"
            f"   Avg WT: {p_wt}s  |  Avg TAT: {p_tat}s\n"
            f"🔸 Giải thuật FCFS:\n"
            f"   Avg WT: {f_wt}s  |  Avg TAT: {f_tat}s\n"
            f"{'—'*45}\n"
            f"{status_wt}\n"
            f"{status_tat}"
        )
        
        compare_label.configure(text=comparison_text, text_color=final_color)
        
    except ValueError as ve:
        compare_label.configure(text=f"⚠️ {ve}", text_color="orange")
    except Exception as e:
        compare_label.configure(text=f"❌ Lỗi hệ thống: {e}", text_color="red")

# --- Layout ---
input_scroll = ctk.CTkScrollableFrame(app, width=500, height=250, label_text="Dữ liệu đầu vào")
input_scroll.pack(pady=10)

ctrl_frame = ctk.CTkFrame(app)
ctrl_frame.pack(pady=10)

ctk.CTkButton(ctrl_frame, text="+ Thêm P", command=add_process, width=100).grid(row=0, column=0, padx=5)
algo_var = ctk.StringVar(value="Priority (Preemptive)")
ctk.CTkOptionMenu(ctrl_frame, variable=algo_var, values=["Priority (Non-Preemptive)", "Priority (Preemptive)"]).grid(row=0, column=1, padx=5)
ctk.CTkButton(ctrl_frame, text="CHẠY", command=run, fg_color="green", width=100).grid(row=0, column=2, padx=5)

compare_label = ctk.CTkLabel(app, text="Bấm CHẠY để xem phân tích so sánh", font=("Arial", 14, "bold"))
compare_label.pack(pady=10)

chart_frame = ctk.CTkFrame(app, width=1000, height=400, fg_color="white")
chart_frame.pack(pady=10, fill="both", expand=True)

app.mainloop()