import json
import os
import statistics

def calculate_metrics(log_file_path):
    if not os.path.exists(log_file_path):
        print(f"❌ Không tìm thấy file log: {log_file_path}")
        return

    latencies = []
    tokens = []
    total_cost = 0.0

    # Đọc file log do IndustryLogger sinh ra
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                
                # Chúng ta chỉ lấy thống kê ở bước AGENT_END (khi Agent trả lời xong)
                if log_entry.get("event") == "AGENT_END" and "latency_sec" in log_entry.get("data", {}):
                    data = log_entry["data"]
                    latencies.append(data["latency_sec"] * 1000) # Đổi giây ra mili-giây (ms)
                    tokens.append(data["total_tokens"])
                    
                    # Tính cost (Ví dụ mô phỏng: $0.01 cho mỗi 1000 tokens)
                    # Bạn có thể thay bằng giá thật của GPT-4o nếu muốn
                    total_cost += (data["total_tokens"] / 1000.0) * 0.01
                    
            except json.JSONDecodeError:
                continue

    if not latencies:
        print("⚠️ Không có dữ liệu AGENT_END nào trong log. Hãy chắc chắn bạn đã chat với bot vài câu.")
        return

    # Tính toán các chỉ số thống kê
    latencies.sort()
    
    # P50 (Median)
    p50_latency = statistics.median(latencies)
    
    # P99 (Lấy giá trị ở vị trí 99%)
    p99_index = int(len(latencies) * 0.99)
    if p99_index >= len(latencies):
        p99_index = len(latencies) - 1
    p99_latency = latencies[p99_index]
    
    avg_tokens = sum(tokens) / len(tokens)

    print("\n" + "="*50)
    print("📊 KẾT QUẢ ĐỂ ĐIỀN VÀO GROUP REPORT (Mục 3)")
    print("="*50)
    print(f"- **Average Latency (P50)**: {p50_latency:.0f}ms")
    print(f"- **Max Latency (P99)**: {p99_latency:.0f}ms")
    print(f"- **Average Tokens per Task**: {avg_tokens:.0f} tokens")
    print(f"- **Total Cost of Test Suite**: ${total_cost:.4f}")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Thay đổi tên file log cho đúng với ngày bạn chạy test
    log_path = "./logs/2026-04-06.log" 
    calculate_metrics(log_path)