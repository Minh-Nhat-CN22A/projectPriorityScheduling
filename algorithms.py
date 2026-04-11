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

def priority_non_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Giải thuật Ưu tiên - Không độc chiếm (Tích hợp chống đói tài nguyên - Aging)
    """
    data = [p.copy() for p in processes]
    n, current_time, completed, gantt = len(data), 0, [], []
    
    while len(completed) < n:
        # Lấy danh sách tiến trình đã đến và chưa chạy xong
        ready = [p for p in data if p['arrival_time'] <= current_time and p not in completed]
        
        if ready:
            # --- LOGIC AGING CHO NON-PREEMPTIVE ---
            if aging_enabled:
                for p in ready:
                    # Tính thời gian thực tế tiến trình đã phải đứng chờ
                    wait_time = current_time - p['arrival_time']
                    # Tính số bậc được tăng (Chia lấy phần nguyên)
                    boost = wait_time // threshold
                    # Cập nhật ưu tiên mới (Không vượt quá mức 1)
                    p['current_priority'] = max(1, p['priority'] - int(boost))
            else:
                for p in ready:
                    p['current_priority'] = p['priority'] # Giữ nguyên nếu tắt Aging

            # --- CHỌN TIẾN TRÌNH CHẠY ---
            # So sánh dựa trên ưu tiên hiện tại (current_priority)
            p = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            # Ghi nhận kết quả
            p['start_time'] = current_time
            p['finish_time'] = current_time + p['burst_time']
            p['turnaround_time'] = p['finish_time'] - p['arrival_time']
            p['waiting_time'] = p['turnaround_time'] - p['burst_time']
            
            gantt.append({"id": p['id'], "start": current_time, "end": p['finish_time']})
            
            # CPU nhảy cóc đến thẳng thời điểm chạy xong
            current_time = p['finish_time']
            completed.append(p)
        else: 
            # CPU rảnh, tăng thời gian lên 1
            current_time += 1
            
    return completed, gantt

def priority_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Giải thuật Ưu tiên - Độc chiếm (Tích hợp chống đói tài nguyên - Aging)
    - aging_enabled: Bật/Tắt tính năng Aging.
    - threshold: Sau bao nhiêu nhịp (giây) chờ thì tăng 1 bậc ưu tiên.
    """
    data = [p.copy() for p in processes]
    for p in data: 
        p['rem'] = p['burst_time']
        p['wait_time_count'] = 0  
        p['current_priority'] = p['priority'] 
        
    n, current_time, completed_count, completed_list, gantt = len(data), 0, 0, [], []
    last_id = None
    
    while completed_count < n:
        ready = [p for p in data if p['arrival_time'] <= current_time and p['rem'] > 0]
        
        if ready:
            # 1. Tìm tiến trình chạy (Dựa trên current_priority)
            p_selected = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            # 2. Xử lý biểu đồ Gantt
            if last_id != p_selected['id']:
                gantt.append({"id": p_selected['id'], "start": current_time, "end": current_time + 1})
            else: 
                gantt[-1]['end'] += 1
                
            p_selected['rem'] -= 1
            last_id = p_selected['id']
            
            # 3. LOGIC AGING ĐÃ ĐƯỢC FIX CỰC CHUẨN
            if aging_enabled:
                for p in ready:
                    # Kẻ nào KHÔNG được chạy mới bị cộng thời gian đợi
                    if p['id'] != p_selected['id']: 
                        p['wait_time_count'] += 1
                        if p['wait_time_count'] >= threshold:
                            if p['current_priority'] > 1: 
                                p['current_priority'] -= 1
                            p['wait_time_count'] = 0
                    else:
                        # Đang chạy thì không tính là đợi
                        p['wait_time_count'] = 0

            # 4. Kiểm tra hoàn thành
            if p_selected['rem'] == 0:
                completed_count += 1
                p_selected['finish_time'] = current_time + 1
                p_selected['turnaround_time'] = p_selected['finish_time'] - p_selected['arrival_time']
                p_selected['waiting_time'] = p_selected['turnaround_time'] - p_selected['burst_time']
                completed_list.append(p_selected)
                last_id = None
        else: 
            current_time += 1
            last_id = None
            
        current_time += 1
        
    return completed_list, gantt