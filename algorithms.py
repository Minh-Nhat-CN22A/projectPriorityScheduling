# algorithms.py - Core logic for scheduling algorithms

def calculate_metrics(completed_processes):
    """
    Calculate average metrics (Waiting Time & Turnaround Time).
    Used to compare the efficiency of different algorithms.
    """
    if not completed_processes: return 0, 0
    # WT = Total waiting time / Number of processes
    avg_wt = sum(p['waiting_time'] for p in completed_processes) / len(completed_processes)
    # TAT = Total turnaround time / Number of processes
    avg_tat = sum(p['turnaround_time'] for p in completed_processes) / len(completed_processes)
    return round(avg_wt, 2), round(avg_tat, 2)

def fcfs_algorithm(processes):
    """
    First-Come, First-Served (FCFS) scheduling algorithm.
    Used as a baseline to compare against Priority algorithms.
    """
    # Create a deep copy of the data to avoid modifying the original input
    data = [p.copy() for p in processes]
    # Sort processes by Arrival Time
    data.sort(key=lambda x: x['arrival_time'])
    
    current_time = 0
    for p in data:
        # If CPU is idle and the next process hasn't arrived, jump the current time
        if current_time < p['arrival_time']: 
            current_time = p['arrival_time']
            
        p['start_time'] = current_time
        p['finish_time'] = current_time + p['burst_time']
        # Turnaround Time = Finish Time - Arrival Time
        p['turnaround_time'] = p['finish_time'] - p['arrival_time']
        # Waiting Time = Turnaround Time - Burst Time
        p['waiting_time'] = p['turnaround_time'] - p['burst_time']
        
        current_time = p['finish_time']
    return data

def priority_non_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Priority Scheduling - NON-PREEMPTIVE.
    Once a process gets the CPU, it runs to completion without interruption.
    """
    data = [p.copy() for p in processes]
    n, current_time, completed, gantt = len(data), 0, [], []
    
    while len(completed) < n:
        # Get all processes that have arrived and are not yet completed (Ready Queue)
        ready = [p for p in data if p['arrival_time'] <= current_time and p not in completed]
        
        if ready:
            # --- AGING LOGIC (Preventing Starvation) ---
            if aging_enabled:
                for p in ready:
                    # Calculate the actual time waited up to the current time
                    wait_time = current_time - p['arrival_time']
                    # Decrease the priority number (increase priority level) for every 'threshold' seconds waited
                    boost = wait_time // threshold
                    p['current_priority'] = max(1, p['priority'] - int(boost))
            else:
                for p in ready:
                    p['current_priority'] = p['priority']

            # --- SELECT PROCESS ---
            # Select the process with the highest priority (lowest current_priority value). 
            # If tied, select the one that arrived first.
            p = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            p['start_time'] = current_time
            p['finish_time'] = current_time + p['burst_time']
            p['turnaround_time'] = p['finish_time'] - p['arrival_time']
            p['waiting_time'] = p['turnaround_time'] - p['burst_time']
            
            gantt.append({"id": p['id'], "start": current_time, "end": p['finish_time']})
            
            # Non-preemptive: Jump time directly to the finish time of the process
            current_time = p['finish_time']
            completed.append(p)
        else: 
            current_time += 1 # CPU is idle, increment time by 1
            
    return completed, gantt

def priority_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Priority Scheduling - PREEMPTIVE.
    CPU checks every second; a higher priority process can preempt the current one.
    """
    data = [p.copy() for p in processes]
    for p in data: 
        p['rem'] = p['burst_time']      # Remaining burst time
        p['wait_time_count'] = 0        # Separate counter to handle aging step-by-step
        p['current_priority'] = p['priority'] 
        
    n, current_time, completed_count, completed_list, gantt = len(data), 0, 0, [], []
    last_id = None
    
    while completed_count < n:
        # Find processes that have arrived and still need execution time (rem > 0)
        ready = [p for p in data if p['arrival_time'] <= current_time and p['rem'] > 0]
        
        if ready:
            # 1. Select the process with the highest priority
            p_selected = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            # 2. Record into Gantt chart (Create a new block if the process changed)
            if last_id != p_selected['id']:
                gantt.append({"id": p_selected['id'], "start": current_time, "end": current_time + 1})
            else: 
                gantt[-1]['end'] += 1 # Extend the existing block if the same process is still running
                
            p_selected['rem'] -= 1
            last_id = p_selected['id']
            
            # 3. CRITICAL AGING LOGIC
            # Only processes WAITING in the ready queue are subject to aging
            if aging_enabled:
                for p in ready:
                    if p['id'] != p_selected['id']: 
                        p['wait_time_count'] += 1
                        # If wait time reaches the threshold, increase priority (decrease priority number)
                        if p['wait_time_count'] >= threshold:
                            if p['current_priority'] > 1: 
                                p['current_priority'] -= 1
                            p['wait_time_count'] = 0 # Reset the wait counter after boosting priority
                    else:
                        p['wait_time_count'] = 0 # The running process is not waiting, so reset its counter

            # 4. When a process completely finishes
            if p_selected['rem'] == 0:
                completed_count += 1
                p_selected['finish_time'] = current_time + 1
                p_selected['turnaround_time'] = p_selected['finish_time'] - p_selected['arrival_time']
                p_selected['waiting_time'] = p_selected['turnaround_time'] - p_selected['burst_time']
                completed_list.append(p_selected)
                last_id = None # Reset so the next Gantt block is created anew
        else: 
            last_id = None
            
        current_time += 1 # Preemptive mode steps forward exactly 1 second at a time
        
    return completed_list, gantt