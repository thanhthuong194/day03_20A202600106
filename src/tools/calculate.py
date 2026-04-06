import pandas as pd
import json

def fetch_interest_rates(bank_name: str, type_rate: str = "online") -> str:
    """
    Công cụ cào dữ liệu lãi suất thực tế từ trang Techcombank
    type_rate: 'online' hoặc 'tai_quay'
    """
    url = "https://techcombank.com/thong-tin/blog/lai-suat-tiet-kiem"
    
    try:
        # Pandas sẽ lấy tất cả các bảng trên trang web
        tables = pd.read_html(url)
        
        # Dựa vào thứ tự trên trang, Bảng 0 thường là bảng ví dụ, 
        # Bảng 1 là Lãi suất tại quầy, Bảng 2 là Lãi suất Online.
        if type_rate == "online":
            df = tables[2] # Bảng số 3 (index 2)
        else:
            df = tables[1] # Bảng số 2 (index 1)
            
        # Làm sạch dữ liệu: Xóa các cột/hàng bị NaN hoặc định dạng lại
        # (Bạn có thể in df ra để xem cấu trúc và map cột cho đúng)
        df.columns = ["Ngan_hang", "1_thang", "3_thang", "6_thang", "12_thang", "18_thang", "24_thang", "36_thang"]
        
        # Tìm ngân hàng theo tên
        # Lọc ra dòng chứa tên ngân hàng (không phân biệt hoa thường)
        bank_data = df[df['Ngan_hang'].str.contains(bank_name, case=False, na=False)]
        
        if bank_data.empty:
            return f"Không tìm thấy dữ liệu cho ngân hàng {bank_name}."
            
        # Chuyển dòng dữ liệu tìm được thành dictionary/JSON
        result = bank_data.to_dict(orient="records")[0]
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return f"Lỗi khi cào dữ liệu: {str(e)}"

# Cấu hình Tool Spec cho ReAct Agent
BANK_SCRAPE_TOOL = {
    "name": "fetch_interest_rates",
    "description": "Lấy bảng lãi suất tiền gửi của các ngân hàng tại Việt Nam (kỳ hạn 1-36 tháng). Truyền vào 2 tham số: bank_name (tên ngân hàng, VD: 'VPBank', 'Vietcombank') và type_rate ('online' hoặc 'tai_quay').",
    "function": fetch_interest_rates
}