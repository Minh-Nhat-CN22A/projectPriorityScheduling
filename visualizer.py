# visualizer.py - Hiển thị mọi mốc Arrival Time
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def draw_gantt_chart(parent_frame, raw_data, gantt_data):
    for widget in parent_frame.winfo_children(): widget.destroy()
    
    # 1. LẤY TẤT CẢ CÁC MỐC THỜI GIAN: Bắt đầu, Kết thúc và cả thời điểm TIẾN TRÌNH ĐẾN
    event_times = sorted(list(set(
        [0] + 
        [s['start'] for s in gantt_data] + 
        [s['end'] for s in gantt_data] +
        [p['arrival_time'] for p in raw_data]
    )))
    
    fig, ax = plt.subplots(figsize=(10, 6)) # Tăng chiều cao để bảng Remaining không bị đè
    colors = list(mcolors.TABLEAU_COLORS.values())
    unique_ids = list(set(p['id'] for p in raw_data))
    color_map = {pid: colors[i % len(colors)] for i, pid in enumerate(unique_ids)}

    # 2. Vẽ biểu đồ Gantt (Giữ nguyên các khối màu)
    for s in gantt_data:
        ax.broken_barh([(s['start'], s['end']-s['start'])], (30, 10), 
                       facecolors=color_map[s['id']], edgecolor='black', linewidth=1)
        ax.text(s['start'] + (s['end']-s['start'])/2, 35, s['id'], 
                ha='center', va='center', color='white', fontweight='bold', fontsize=12)

    # 3. LOGIC TÍNH TOÁN VÀ VẼ 3 DÒNG THÔNG TIN (TIME, ARRIVED, REMAINING)
    current_rem = {p['id']: p['burst_time'] for p in raw_data}
    
    for i in range(len(event_times)):
        t = event_times[i]
        
        # Dòng 1: Time (Ngay dưới vạch kẻ)
        ax.text(t, 25, str(t), ha='center', va='top', fontsize=10, fontweight='bold')
        ax.axvline(x=t, ymin=0.4, ymax=0.6, color='black', linestyle='--', alpha=0.3) # Vạch kẻ phụ

        # Dòng 2: Arrived Process (Ai đến tại thời điểm t)
        arrived = [p['id'] for p in raw_data if p['arrival_time'] == t]
        if arrived:
            ax.text(t, 20, ", ".join(arrived), ha='center', va='top', fontsize=9, color='blue', fontweight='bold')
        
        # Dòng 3: Remaining Time (Trạng thái tại mốc t)
        status = []
        # Sắp xếp theo ID để hiển thị P1, P2... cho gọn
        for p in sorted(raw_data, key=lambda x: x['id']):
            if p['arrival_time'] <= t and current_rem[p['id']] > 0:
                status.append(f"{p['id']}({current_rem[p['id']]})")
        
        if status:
            # Dùng \n để các tiến trình nằm dọc giống hình mẫu của Nhật
            ax.text(t, 15, "\n".join(status), ha='center', va='top', fontsize=8, color='green')

        # CẬP NHẬT REMAINING TIME cho đoạn tiếp theo
        if i < len(event_times) - 1:
            next_t = event_times[i+1]
            duration = next_t - t
            # Tìm xem trong khoảng [t, next_t], CPU đang chạy ai
            for s in gantt_data:
                if s['start'] <= t and s['end'] >= next_t:
                    current_rem[s['id']] -= duration
                    break

    # Cấu hình khung nhìn
    ax.set_xlim(-1, max(event_times) + 2)
    ax.set_ylim(0, 50)
    ax.axis('off') # Ẩn các trục mặc định
    
    # Nhãn tiêu đề bên trái
    ax.text(-0.5, 25, "Time:", ha='right', va='top', fontweight='bold')
    ax.text(-0.5, 20, "Arrived:", ha='right', va='top', fontweight='bold')
    ax.text(-0.5, 15, "Remaining:", ha='right', va='top', fontweight='bold')

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)