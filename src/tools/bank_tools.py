import pandas as pd
import io
import re

def extract_number(text):
    """Hàm phụ trợ để tách lấy con số lãi suất từ chuỗi rác"""
    match = re.search(r"(\d+\.\d+|\d+)", str(text))
    if match:
        return match.group(1)
    return str(text)

def fetch_interest_rates(bank_name: str = "all", type_rate: str = "online") -> str:
    """
    Công cụ cào dữ liệu lãi suất từ Techcombank và trả về dạng CSV.
    - bank_name: Tên ngân hàng (VD: 'VPBank') hoặc truyền 'all' để lấy tất cả.
    - type_rate: 'online' hoặc 'tai_quay'
    """
    url = "https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem"
    
    try:
        # Pandas sẽ lấy tất cả các bảng trên trang web
        tables = pd.read_html(url)
        
        # Tự động lọc ra những bảng có đúng 8 cột (bảng lãi suất chuẩn)
        valid_tables = [table for table in tables if len(table.columns) == 8]
        
        if len(valid_tables) < 2:
            return "Lỗi: Không tìm thấy đủ bảng lãi suất trên web."
            
        # Trong các bảng chuẩn: Bảng 1 (index 0) là Tại quầy, Bảng 2 (index 1) là Online
        if type_rate == "online":
            df = valid_tables[1].copy()
        else:
            df = valid_tables[0].copy()
            
        # Gán tên cột
        df.columns = ["Ngan_hang", "1_thang", "3_thang", "6_thang", "12_thang", "18_thang", "24_thang", "36_thang"]
        
        # Làm sạch dữ liệu: Chỉ giữ lại các con số lãi suất
        cols_to_clean = ["1_thang", "3_thang", "6_thang", "12_thang", "18_thang", "24_thang", "36_thang"]
        for col in cols_to_clean:
            df[col] = df[col].apply(extract_number)
        
        # Nếu người dùng muốn lọc một ngân hàng cụ thể
        if bank_name.lower() != "all":
            df = df[df['Ngan_hang'].str.contains(bank_name, case=False, na=False)]
            if df.empty:
                return f"Lỗi: Không tìm thấy dữ liệu cho ngân hàng {bank_name}."
                
        # Trả về toàn bộ dữ liệu dưới định dạng CSV (chuỗi văn bản)
        return df.to_csv(index=False)
        
    except Exception as e:
        return f"Lỗi khi cào dữ liệu: {str(e)}"

# Cấu hình Tool Spec cho ReAct Agent
BANK_SCRAPE_TOOL = {
    "name": "fetch_interest_rates",
    "description": "Lấy bảng lãi suất tiền gửi dạng CSV. Truyền bank_name='all' để lấy toàn bộ, hoặc tên riêng (VD: 'MBBank'). Tham số type_rate='online' hoặc 'tai_quay'.",
    "function": fetch_interest_rates
}

# ========================================================
# CODE TEST VỚI PANDAS ĐỂ VIEW CSV
# ========================================================
if __name__ == "__main__":
    print("=== BẮT ĐẦU TEST CÔNG CỤ (TRẢ VỀ CSV) ===")
    
    # 1. Gọi tool để lấy data dưới dạng chuỗi CSV (giả lập việc Agent dùng tool)
    print("\n1. Đang cào toàn bộ dữ liệu lãi suất ONLINE...")
    csv_string = fetch_interest_rates(bank_name="all", type_rate="online")
    
    # 2. Dùng Pandas để view chuỗi CSV đó thay vì in chay
    if not csv_string.startswith("Lỗi"):
        # Dùng io.StringIO để biến chuỗi string thành một file-like object cho pandas đọc
        df_view = pd.read_csv(io.StringIO(csv_string))
        
        print("\n>> DỮ LIỆU ĐÃ ĐƯỢC CHUYỂN THÀNH PANDAS DATAFRAME ĐỂ VIEW:\n")
        
        # Cài đặt để hiển thị đẹp hơn trên terminal
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        # In ra 10 ngân hàng đầu tiên để kiểm tra
        print(df_view.head(10))
        print(f"\n[Thông tin] Đã lấy thành công {len(df_view)} ngân hàng.")
    else:
        print(csv_string)
        
    print("\n=== HOÀN THÀNH TEST ===")