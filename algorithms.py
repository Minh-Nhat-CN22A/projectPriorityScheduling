# algorithms.py - Bộ não xử lý các giải thuật lập lịch

def calculate_metrics(completed_processes):
    """
    Tính toán các chỉ số trung bình (Waiting Time & Turnaround Time).
    Dùng để so sánh hiệu quả giữa các thuật toán.
    """
    if not completed_processes: return 0, 0
    # WT = Tổng thời gian chờ / Số tiến trình
    avg_wt = sum(p['waiting_time'] for p in completed_processes) / len(completed_processes)
    # TAT = Tổng thời gian hoàn thành từ lúc đến / Số tiến trình
    avg_tat = sum(p['turnaround_time'] for p in completed_processes) / len(completed_processes)
    return round(avg_wt, 2), round(avg_tat, 2)

def fcfs_algorithm(processes):
    """
    Giải thuật First-Come, First-Served (Ai đến trước phục vụ trước).
    Dùng làm mốc (Baseline) để so sánh với thuật toán Priority.
    """
    # Tạo bản sao dữ liệu để không làm ảnh hưởng đến dữ liệu gốc
    data = [p.copy() for p in processes]
    # Sắp xếp theo thời điểm đến (Arrival Time)
    data.sort(key=lambda x: x['arrival_time'])
    
    current_time = 0
    for p in data:
        # Nếu CPU rảnh mà tiến trình chưa đến, CPU phải đợi (nhảy mốc thời gian)
        if current_time < p['arrival_time']: 
            current_time = p['arrival_time']
            
        p['start_time'] = current_time
        p['finish_time'] = current_time + p['burst_time']
        # Turnaround Time = Thời điểm xong - Thời điểm đến
        p['turnaround_time'] = p['finish_time'] - p['arrival_time']
        # Waiting Time = Turnaround Time - Burst Time (thời gian thực chạy)
        p['waiting_time'] = p['turnaround_time'] - p['burst_time']
        
        current_time = p['finish_time']
    return data

def priority_non_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Giải thuật Ưu tiên - KHÔNG ĐỘC CHIẾM (Non-Preemptive).
    Tiến trình đã cầm CPU là chạy cho xong, không ai được cướp.
    """
    data = [p.copy() for p in processes]
    n, current_time, completed, gantt = len(data), 0, [], []
    
    while len(completed) < n:
        # Lấy các tiến trình đã có mặt trong hàng đợi Ready
        ready = [p for p in data if p['arrival_time'] <= current_time and p not in completed]
        
        if ready:
            # --- LOGIC AGING (Chống đói tài nguyên) ---
            if aging_enabled:
                for p in ready:
                    # Tính thời gian đã đợi thực tế tính đến hiện tại
                    wait_time = current_time - p['arrival_time']
                    # Cứ đợi đủ 'threshold' giây thì giảm số Priority (tức là tăng mức ưu tiên)
                    boost = wait_time // threshold
                    p['current_priority'] = max(1, p['priority'] - int(boost))
            else:
                for p in ready:
                    p['current_priority'] = p['priority']

            # --- CHỌN TIẾN TRÌNH ---
            # Ưu tiên current_priority nhỏ nhất. Nếu bằng nhau thì ai đến trước (arrival) chạy trước.
            p = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            p['start_time'] = current_time
            p['finish_time'] = current_time + p['burst_time']
            p['turnaround_time'] = p['finish_time'] - p['arrival_time']
            p['waiting_time'] = p['turnaround_time'] - p['burst_time']
            
            gantt.append({"id": p['id'], "start": current_time, "end": p['finish_time']})
            
            # Non-preemptive: Nhảy vọt thời gian đến lúc xong luôn
            current_time = p['finish_time']
            completed.append(p)
        else: 
            current_time += 1 # Không có ai thì CPU chạy không
            
    return completed, gantt

def priority_preemptive(processes, aging_enabled=False, threshold=5):
    """
    Giải thuật Ưu tiên - ĐỘC CHIẾM (Preemptive).
    CPU kiểm tra mỗi giây, ai ưu tiên cao hơn sẽ nhảy vào 'cướp' CPU ngay.
    """
    data = [p.copy() for p in processes]
    for p in data: 
        p['rem'] = p['burst_time']      # Thời gian còn lại cần chạy
        p['wait_time_count'] = 0        # Bộ đếm riêng để xử lý Aging mỗi giây
        p['current_priority'] = p['priority'] 
        
    n, current_time, completed_count, completed_list, gantt = len(data), 0, 0, [], []
    last_id = None
    
    while completed_count < n:
        # Tìm những anh đã đến và còn thời gian chạy (rem > 0)
        ready = [p for p in data if p['arrival_time'] <= current_time and p['rem'] > 0]
        
        if ready:
            # 1. Chọn tiến trình VIP nhất hiện tại
            p_selected = min(ready, key=lambda x: (x['current_priority'], x['arrival_time']))
            
            # 2. Ghi nhận vào biểu đồ Gantt (Nếu đổi tiến trình thì tạo khối mới)
            if last_id != p_selected['id']:
                gantt.append({"id": p_selected['id'], "start": current_time, "end": current_time + 1})
            else: 
                gantt[-1]['end'] += 1 # Cùng một anh thì kéo dài khối cũ ra
                
            p_selected['rem'] -= 1
            last_id = p_selected['id']
            
            # 3. LOGIC AGING CỰC KỲ QUAN TRỌNG
            # Chỉ những anh đang ĐỢI trong hàng đợi mới được tính Aging
            if aging_enabled:
                for p in ready:
                    if p['id'] != p_selected['id']: 
                        p['wait_time_count'] += 1
                        # Nếu đợi đủ ngưỡng, tăng mức VIP (giảm số priority)
                        if p['wait_time_count'] >= threshold:
                            if p['current_priority'] > 1: 
                                p['current_priority'] -= 1
                            p['wait_time_count'] = 0 # Reset bộ đếm sau khi tăng bậc
                    else:
                        p['wait_time_count'] = 0 # Đang được chạy thì không tính là đợi

            # 4. Khi một anh chạy xong hoàn toàn
            if p_selected['rem'] == 0:
                completed_count += 1
                p_selected['finish_time'] = current_time + 1
                p_selected['turnaround_time'] = p_selected['finish_time'] - p_selected['arrival_time']
                p_selected['waiting_time'] = p_selected['turnaround_time'] - p_selected['burst_time']
                completed_list.append(p_selected)
                last_id = None # Reset để khối Gantt tiếp theo được tạo mới
        else: 
            last_id = None
            
        current_time += 1 # Chế độ Preemptive chạy từng nhịp 1 giây
        
    return completed_list, gantt