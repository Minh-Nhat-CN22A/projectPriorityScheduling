# algorithms.py - Bộ não xử lý các giải thuật lập lịch

def calculate_metrics(completed_processes):
    """Tính Avg WT và Avg TAT từ danh sách kết quả"""
    if not completed_processes: return 0, 0
    avg_wt = sum(p['waiting_time'] for p in completed_processes) / len(completed_processes)
    avg_tat = sum(p['turnaround_time'] for p in completed_processes) / len(completed_processes)
    return round(avg_wt, 2), round(avg_tat, 2)

def fcfs_algorithm(processes):
    """FCFS dùng để làm mốc so sánh hiệu quả"""
    data = [p.copy() for p in processes]
    data.sort(key=lambda x: x['arrival_time'])
    current_time = 0
    for p in data:
        if current_time < p['arrival_time']: current_time = p['arrival_time']
        p['start_time'] = current_time
        p['finish_time'] = current_time + p['burst_time']
        p['turnaround_time'] = p['finish_time'] - p['arrival_time']
        p['waiting_time'] = p['turnaround_time'] - p['burst_time']
        current_time = p['finish_time']
    return data

def priority_non_preemptive(processes):
    """Giải thuật Ưu tiên - Không độc chiếm"""
    data = [p.copy() for p in processes]
    n, current_time, completed, gantt = len(data), 0, [], []
    while len(completed) < n:
        ready = [p for p in data if p['arrival_time'] <= current_time and p not in completed]
        if ready:
            p = min(ready, key=lambda x: (x['priority'], x['arrival_time']))
            p['start_time'] = current_time
            p['finish_time'] = current_time + p['burst_time']
            p['turnaround_time'] = p['finish_time'] - p['arrival_time']
            p['waiting_time'] = p['turnaround_time'] - p['burst_time']
            gantt.append({"id": p['id'], "start": current_time, "end": p['finish_time']})
            current_time = p['finish_time']
            completed.append(p)
        else: current_time += 1
    return completed, gantt

def priority_preemptive(processes):
    """Giải thuật Ưu tiên - Độc chiếm (Phân đoạn khi có ưu tiên cao hơn đến)"""
    data = [p.copy() for p in processes]
    for p in data: p['rem'] = p['burst_time']
    n, current_time, completed_count, completed_list, gantt = len(data), 0, 0, [], []
    last_id = None
    while completed_count < n:
        ready = [p for p in data if p['arrival_time'] <= current_time and p['rem'] > 0]
        if ready:
            p = min(ready, key=lambda x: (x['priority'], x['arrival_time']))
            if last_id != p['id']:
                gantt.append({"id": p['id'], "start": current_time, "end": current_time + 1})
            else: gantt[-1]['end'] += 1
            p['rem'] -= 1
            last_id = p['id']
            if p['rem'] == 0:
                completed_count += 1
                p['finish_time'] = current_time + 1
                p['turnaround_time'] = p['finish_time'] - p['arrival_time']
                p['waiting_time'] = p['turnaround_time'] - p['burst_time']
                completed_list.append(p)
                last_id = None
        else: 
            current_time += 1
            last_id = None
        current_time += 1
    return completed_list, gantt