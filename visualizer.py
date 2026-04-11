# visualizer.py
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def draw_gantt_chart(parent_frame, raw_data, gantt_data, aging_enabled=False, threshold=5):
    for widget in parent_frame.winfo_children(): widget.destroy()
    
    event_times = sorted(list(set(
        [0] + 
        [s['start'] for s in gantt_data] + 
        [s['end'] for s in gantt_data] +
        [p['arrival_time'] for p in raw_data]
    )))
    
    fig, ax = plt.subplots(figsize=(10, 6.5)) # Tăng chiều cao thêm một chút
    colors = list(mcolors.TABLEAU_COLORS.values())
    unique_ids = list(set(p['id'] for p in raw_data))
    color_map = {pid: colors[i % len(colors)] for i, pid in enumerate(unique_ids)}

    for s in gantt_data:
        ax.broken_barh([(s['start'], s['end']-s['start'])], (35, 10), 
                       facecolors=color_map[s['id']], edgecolor='black', linewidth=1)
        ax.text(s['start'] + (s['end']-s['start'])/2, 40, s['id'], 
                ha='center', va='center', color='white', fontweight='bold', fontsize=12)

    current_rem = {p['id']: p['burst_time'] for p in raw_data}
    
    for i in range(len(event_times)):
        t = event_times[i]
        
        ax.text(t, 30, str(t), ha='center', va='top', fontsize=10, fontweight='bold')
        ax.axvline(x=t, ymin=0.3, ymax=0.7, color='black', linestyle='--', alpha=0.3)

        arrived = [p['id'] for p in raw_data if p['arrival_time'] == t]
        if arrived:
            ax.text(t, 25, ", ".join(arrived), ha='center', va='top', fontsize=9, color='blue', fontweight='bold')
        
        status_rem = []
        status_prio = [] # MẢNG MỚI: Chứa thông tin Priority
        
        for p in sorted(raw_data, key=lambda x: x['id']):
            if p['arrival_time'] <= t and current_rem[p['id']] > 0:
                # 1. Thêm vào mảng Remaining
                status_rem.append(f"{p['id']}({current_rem[p['id']]})")
                
                # 2. TÍNH TOÁN AGING CHO DÒNG PRIORITY
                current_prio = p['priority']
                if aging_enabled:
                    # Tính tổng thời gian đã được chạy từ lúc đến cho tới mốc t
                    run_time = sum([min(s['end'], t) - max(s['start'], p['arrival_time']) 
                                  for s in gantt_data if s['id'] == p['id'] and s['start'] < t])
                    # Tính thời gian phải đứng chờ (Wait Time)
                    wait_time = max(0, t - p['arrival_time'] - run_time)
                    
                    # Cộng điểm ưu tiên (giảm số) dựa trên số lần vượt threshold
                    boost = int(wait_time // threshold)
                    current_prio = max(1, p['priority'] - boost)
                
                status_prio.append(f"{p['id']}({current_prio})")
        
        if status_rem:
            ax.text(t, 20, "\n".join(status_rem), ha='center', va='top', fontsize=8, color='green')
        if status_prio:
            ax.text(t, 10, "\n".join(status_prio), ha='center', va='top', fontsize=8, color='purple', fontweight='bold')

        if i < len(event_times) - 1:
            next_t = event_times[i+1]
            duration = next_t - t
            for s in gantt_data:
                if s['start'] <= t and s['end'] >= next_t:
                    current_rem[s['id']] -= duration
                    break

    ax.set_xlim(-1, max(event_times) + 2)
    ax.set_ylim(0, 55)
    ax.axis('off')
    
    ax.text(-0.5, 30, "Time:", ha='right', va='top', fontweight='bold')
    ax.text(-0.5, 25, "Arrived:", ha='right', va='top', fontweight='bold')
    ax.text(-0.5, 20, "Remaining:", ha='right', va='top', fontweight='bold')
    ax.text(-0.5, 10, "Priority:", ha='right', va='top', fontweight='bold', color='purple') # THÊM NHÃN NÀY

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)