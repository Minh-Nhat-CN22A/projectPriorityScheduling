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
    
    fig, ax = plt.subplots(figsize=(10, 6.5)) # Slightly increased height
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
        status_prio = [] # NEW ARRAY: Contains Priority information
        
        for p in sorted(raw_data, key=lambda x: x['id']):
            if p['arrival_time'] <= t and current_rem[p['id']] > 0:
                # 1. Add to Remaining array
                status_rem.append(f"{p['id']}({current_rem[p['id']]})")
                
                # 2. CALCULATE AGING FOR PRIORITY ROW
                current_prio = p['priority']
                if aging_enabled:
                    # Calculate total time executed since arrival up to time t
                    run_time = sum([min(s['end'], t) - max(s['start'], p['arrival_time']) 
                                  for s in gantt_data if s['id'] == p['id'] and s['start'] < t])
                    # Calculate total waiting time
                    wait_time = max(0, t - p['arrival_time'] - run_time)
                    
                    # Boost priority (decrease number) based on threshold
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
    ax.text(-0.5, 10, "Priority:", ha='right', va='top', fontweight='bold', color='purple') # ADDED THIS LABEL

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
def draw_comparison_chart(parent_frame, p_wt, p_tat, f_wt, f_tat, mode_name):
    """Draw a bar chart comparing WT and TAT between Priority and FCFS"""
    for widget in parent_frame.winfo_children(): widget.destroy()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Data
    labels = ['Average Waiting Time (WT)', 'Average Turnaround Time (TAT)']
    priority_scores = [p_wt, p_tat]
    fcfs_scores = [f_wt, f_tat]
    
    x = [0, 1]  # Position of bar groups
    width = 0.35  # Width of bars

    # Draw bars
    bars1 = ax.bar([i - width/2 for i in x], priority_scores, width, label=mode_name, color='#3498db') # Blue
    bars2 = ax.bar([i + width/2 for i in x], fcfs_scores, width, label='FCFS', color='#e74c3c') # Red

    # Chart formatting
    ax.set_ylabel('Time (Seconds)', fontweight='bold')
    ax.set_title('ALGORITHM PERFORMANCE COMPARISON', fontweight='bold', fontsize=14, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight='bold')
    ax.legend()

    # Display values on top of each bar
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}s',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # Offset text up by 3 points
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold')

    add_labels(bars1)
    add_labels(bars2)

    # Hide top and right spines for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)