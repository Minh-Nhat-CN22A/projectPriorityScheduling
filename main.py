# main.py - Main application entry point
import customtkinter as ctk
from algorithms import *
from ui_components import create_input_row
from visualizer import draw_gantt_chart, draw_comparison_chart
from animator import RealtimeSimulator  # Import animation module

# --- APP INITIALIZATION ---
app = ctk.CTk()
app.title("Priority Scheduling Simulator")
app.geometry("1100x850") 

# --- GLOBAL VARIABLES ---
entries = []
last_simulation_data = None  # Stores calculated data to pass to the Simulation Popup

# --- EVENT HANDLERS ---
def delete_row(frame_to_remove):
    """Remove input row from the list and the UI"""
    for entry in entries:
        if entry['frame'] == frame_to_remove:
            entry['frame'].destroy()
            entries.remove(entry)
            break

def add_process():
    """Add a new input row"""
    idx = len(entries) + 1
    new_entry = create_input_row(input_scroll, idx, delete_row)
    entries.append(new_entry)

def open_animation():
    """Open the Real-time simulation popup window"""
    global last_simulation_data
    if last_simulation_data is None:
        compare_label.configure(text="⚠️ Please click RUN first to generate simulation data!", text_color="orange")
        return
    
    # Initialize the Simulator Window with the newly calculated data
    RealtimeSimulator(
        app, 
        last_simulation_data['raw_data'], 
        last_simulation_data['gantt'], 
        last_simulation_data['aging'], 
        last_simulation_data['threshold']
    )

def run():
    """Core function to run the algorithm, draw charts, and analyze results"""
    global last_simulation_data
    
    try:
        raw_data = []
        for i, e in enumerate(entries):
            if not e['arrival'].get() or not e['burst'].get() or not e['priority'].get():
                raise ValueError(f"Process P{i+1} is missing data!")
                
            raw_data.append({
                "id": f"P{i+1}",
                "arrival_time": int(e['arrival'].get()),
                "burst_time": int(e['burst'].get()),
                "priority": int(e['priority'].get())
            })
        
        if not raw_data:
            compare_label.configure(text="Please add at least one process!", text_color="orange")
            return

        # --- FETCH AGING PARAMETERS FROM UI ---
        is_aging_enabled = aging_var.get()
        try:
            aging_threshold = int(threshold_var.get())
            if aging_threshold <= 0: raise ValueError
        except ValueError:
            raise ValueError("Aging threshold must be an integer greater than 0!")

        # 1. Run Priority based on the selected mode
        mode = algo_var.get()
        if mode == "Priority (Non-Preemptive)":
            res_p, gantt = priority_non_preemptive(raw_data, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        else:
            res_p, gantt = priority_preemptive(raw_data, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        
        # 2. Run FCFS in the background to establish a baseline for comparison
        res_f = fcfs_algorithm(raw_data)
        
        # --- STORE DATA FOR REAL-TIME SIMULATION ---
        last_simulation_data = {
            'raw_data': raw_data,
            'gantt': gantt,
            'aging': is_aging_enabled,
            'threshold': aging_threshold
        }
        
        # 3. Draw Gantt Chart (In Tab 1)
        draw_gantt_chart(tab_gantt, raw_data, gantt, aging_enabled=is_aging_enabled, threshold=aging_threshold)
        
        # 4. Calculate metrics
        p_wt, p_tat = calculate_metrics(res_p)
        f_wt, f_tat = calculate_metrics(res_f)
        
        # 5. Draw Comparison Bar Chart (In Tab 2)
        draw_comparison_chart(chart_report_frame, p_wt, p_tat, f_wt, f_tat, mode)

        # 6. Percentage Calculation & AI-like Insight Generation
        diff_wt = round(((f_wt - p_wt) / f_wt) * 100, 1) if f_wt != 0 else 0
        diff_tat = round(((f_tat - p_tat) / f_tat) * 100, 1) if f_tat != 0 else 0

        # Efficiency Gap Analysis
        if diff_wt > 0 and diff_tat > 0:
            insight = "🌟 FULL OPTIMIZATION: The current Priority algorithm outperforms FCFS in both metrics. Suitable for systems requiring rapid response for critical tasks without degrading overall throughput."
            final_color = "#2ECC71"
        elif diff_wt > 0 and diff_tat <= 0:
            insight = "⚖️ TRADE-OFF: Priority yields faster average response (lower WT) but reduces overall throughput (higher TAT due to preemptions or large processes). Suitable for highly interactive systems."
            final_color = "#F1C40F"
        elif diff_wt < 0:
            insight = "⚠️ LOW EFFICIENCY: Priority is performing worse than FCFS. This is often due to large VIP processes monopolizing the CPU, causing 'Starvation' for others. Consider adjusting priorities or enabling Aging."
            final_color = "#E74C3C"
        else:
            insight = "Performance is equivalent to FCFS."
            final_color = "white"

        comparison_text = (
            f"📊 EFFICIENCY GAP:\n"
            f"{'—'*50}\n"
            f"👉 WT Efficiency : {'Better' if diff_wt >= 0 else 'Worse'} than FCFS by {abs(diff_wt)}%\n"
            f"👉 TAT Efficiency: {'Better' if diff_tat >= 0 else 'Worse'} than FCFS by {abs(diff_tat)}%\n\n"
            f"💡 CONCLUSION:\n{insight}"
        )
        
        compare_label.configure(text=comparison_text, text_color=final_color)
        
    except ValueError as ve:
        compare_label.configure(text=f"⚠️ {ve}", text_color="orange")
    except Exception as e:
        compare_label.configure(text=f"❌ System Error: {e}", text_color="red")


# ==========================================
# --- UI COMPONENTS (LAYOUT) ---
# ==========================================

# 1. Input Area
input_scroll = ctk.CTkScrollableFrame(app, width=500, height=250, label_text="Input Data")
input_scroll.pack(pady=10)

# 2. Control Panel
ctrl_frame = ctk.CTkFrame(app)
ctrl_frame.pack(pady=10)

ctk.CTkButton(ctrl_frame, text="+ Add Process", command=add_process, width=100).grid(row=0, column=0, padx=5, pady=5)

algo_var = ctk.StringVar(value="Priority (Preemptive)")
ctk.CTkOptionMenu(ctrl_frame, variable=algo_var, values=["Priority (Non-Preemptive)", "Priority (Preemptive)"]).grid(row=0, column=1, padx=5, pady=5)

ctk.CTkButton(ctrl_frame, text="RUN", command=run, fg_color="green", width=100).grid(row=0, column=2, padx=5, pady=5)

# Button to trigger Real-time Simulation
ctk.CTkButton(ctrl_frame, text="Simulate", command=open_animation, fg_color="#3498db", width=150).grid(row=0, column=3, padx=10, pady=5)

# 3. Aging Configuration Area
aging_frame = ctk.CTkFrame(app, fg_color="transparent")
aging_frame.pack(pady=5)

aging_var = ctk.BooleanVar(value=False)
aging_checkbox = ctk.CTkCheckBox(aging_frame, text="Enable Aging (Prevent Starvation)", variable=aging_var, text_color="#F1C40F")
aging_checkbox.pack(side="left", padx=10)

ctk.CTkLabel(aging_frame, text="Threshold (s):").pack(side="left")
threshold_var = ctk.StringVar(value="5")
threshold_entry = ctk.CTkEntry(aging_frame, textvariable=threshold_var, width=50)
threshold_entry.pack(side="left", padx=5)

# 4. Results Display Area (Using Tabview)
tabview = ctk.CTkTabview(app, width=1050, height=450)
tabview.pack(pady=10, fill="both", expand=True, padx=20)

tab_gantt = tabview.add("Gantt Chart & Timeline")
tab_report = tabview.add("Performance Report")

# Internal Layout for "Performance Report" Tab
report_text_frame = ctk.CTkFrame(tab_report, width=400, fg_color="transparent")
report_text_frame.pack(side="left", fill="both", expand=False, padx=20, pady=20)

compare_label = ctk.CTkLabel(report_text_frame, text="Click RUN to view comparative analysis", 
                             font=("Arial", 14, "bold"), justify="left", wraplength=350)
compare_label.pack(pady=20, anchor="w")

chart_report_frame = ctk.CTkFrame(tab_report, fg_color="white")
chart_report_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Run application loop
app.mainloop()