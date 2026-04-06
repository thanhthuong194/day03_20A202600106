# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: LÊ VĂN TÙNG
- **Student ID**: 20a202600111
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Trong bài lab số 3 này, mình đã tham gia code 1 tool chính là __bank_tools__ dùng để lấy các dữ liệu lãi suất ngân hàng thông qua web __webgia.com__, ngoài ra còn code module __agent.py__ để có thể loop cũng như gọi tool cho đúng*

- **Modules Implementated**: src/tools/bank_tools.py
- **Code Highlights**: Tất cả __*from line 1 to line 136*__
- **Documentation**: Khi người dùng yêu cầu trích xuất thông tin về lãi suất. LLM sẽ phân tích và nếu đủ tốt sẽ gọi tool __*bank_tools.py*__. Nếu như chỉ định cụ thể một ngân hàng như 'ACB' thì sẽ truyền vào name là 'ACB', còn nếu yêu cầu tất cả thì sẽ truyền vào "all". Các option detail khác ví dụ như "tại quầy" hoặc "online", "kỳ hạn '_xx_' tháng" nếu có cũng sẽ được truyền vào. Trả về sẽ là một file csv bao gồm các trường dữ liệu cần thiết cho tool thứ 2 như tính toán, hoặc đơn giản là in ra màn hình để người dùng có thể xem.

- **Modules Implementated**: src/agent/agent.py
- **Code Highlights**: hàm **run** và hàm **get_system_prompt**  __*from line 20 to line 112*__
- **Documentation**: Define prompt cho ReAct Agent và viết vòng lặp, thêm history chat cho Agent. 
---

## II. Debugging Case Study (10 Points)

bug 1:
- **Problem Description**: Website chặn request khiến việc thu thập dữ liệu thất bại hoặc không ổn định (bị block, trả về HTML khác, hoặc yêu cầu xác thực)
- **Log Source**: 
- **Diagnosis**: Nguyên nhân chủ yếu đến từ phía website (anti-bot protection), không phải do model. Các request gửi đi thiếu header (User-Agent, cookies,...) hoặc gửi quá nhiều request trong thời gian ngắn nên bị phát hiện là bot
- **Solution**:  
```
rowser = p.chromium.launch(headless=True)
page = browser.new_page(user_agent="Mozilla/5.0...")
```
Bug 2:
- **Problem Description**: Khi tool call với yêu cầu lấy toàn bộ dữ liệu (__all__), model không truyền đúng tham số mà trả về thiếu hoặc sai format.
- **Log Source**: name: *ngân hàng A, type tại quầy*
- **Diagnosis**: Do sử dụng model gpt-4o-mini, khả năng hiểu prompt và tuân thủ instruction chưa đủ tốt, đặc biệt với các yêu cầu mang tính quy ước như __all__. Đây là vấn đề từ model limitation kết hợp với prompt chưa đủ rõ ràng
- **Solution**: Đổi model mạnh hơn(gpt-4o), cập nhật hàm run để nối thêm chat_history


---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: Khối `Thought` đóng vai trò như một "bộ đệm suy nghĩ" giúp Agent vạch ra kế hoạch rõ ràng trước khi hành động. So với một Chatbot truyền thống thường sinh ra câu trả lời ngay lập tức (dễ dẫn đến ảo giác - hallucination với các con số tài chính), ReAct Agent nhờ có `Thought` sẽ tự phân tích được: *"Để trả lời câu hỏi này, mình cần biết lãi suất hiện tại -> Mình phải gọi tool bank_tools -> Mình cần tham số tên ngân hàng và hình thức gửi"*. Điều này đặc biệt quan trọng trong lĩnh vực tài chính, nơi dữ liệu cần sự chính xác tuyệt đối theo thời gian thực thay vì dựa vào dữ liệu huấn luyện cũ.

2. **Reliability**: Agent thực tế lại hoạt động *tệ hơn* Chatbot trong các tình huống: 
   - **Phụ thuộc vào Tool/Môi trường:** Khi website thay đổi cấu trúc HTML hoặc tăng cường anti-bot (như Bug 1), tool bị sập khiến Agent kẹt trong vòng lặp lỗi hoặc đưa ra thông báo kỹ thuật khó hiểu cho người dùng. Trong khi đó, Chatbot thuần túy có thể từ chối khéo léo hoặc đưa ra lời khuyên chung chung.
   - **Rủi ro vòng lặp vô tận (Infinite Loop):** Nếu System Prompt không đủ chặt chẽ hoặc model bị "quên" ngữ cảnh (như Bug 2 không chịu truyền tham số `all`), Agent sẽ liên tục hỏi đi hỏi lại người dùng hoặc gọi sai tool cho đến khi cạn kiệt số bước (`max_steps`), gây tốn kém token và độ trễ cao (high latency).

3. **Observation**: Phản hồi từ môi trường (Observation) chính là mỏ neo giữ cho Agent đi đúng hướng. Ví dụ: Khi Agent truyền sai tên ngân hàng vào tool, thay vì bị crash, tool trả về Observation là danh sách các ngân hàng hợp lệ. LLM đọc được Observation này, tự động nhận ra lỗi trong khối `Thought` tiếp theo và phản hồi lại người dùng: *"Tôi không tìm thấy ngân hàng bạn yêu cầu, bạn có thể chọn trong các ngân hàng sau..."*. Nó tạo ra khả năng tự sửa sai (self-correction) rất tự nhiên.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
  - Chuyển đổi công cụ `bank_tools` sang dạng bất đồng bộ (Asynchronous) sử dụng `asyncio` và `playwright.async_api` để có thể phục vụ nhiều người dùng cùng lúc (concurrent requests) mà không bị nghẽn (blocking).
  - Tích hợp hệ thống Caching (như Redis). Dữ liệu lãi suất ngân hàng thường chỉ cập nhật theo ngày/tuần, nên việc cache lại kết quả của lần chạy tool trước đó sẽ giảm thiểu số lượng request lên website gốc, tránh bị block IP và giảm đáng kể độ trễ (latency) cho người dùng.
- **Safety**: 
  - Áp dụng các thư viện Data Validation như `Pydantic` để kiểm tra nghiêm ngặt kiểu dữ liệu của các arguments do LLM sinh ra trước khi thực thi tool, tránh lỗi Injection hoặc Crash hệ thống.
  - Thiết lập một cấu trúc Supervisor/Guardrail đơn giản để kiểm duyệt nội dung đầu ra của Agent, đảm bảo Agent không đưa ra các "lời khuyên đầu tư" sai lệch hoặc cam kết lợi nhuận trái quy định pháp luật.
- **Performance**: 
  - **Tối ưu hóa Token & Cost:** Xây dựng cơ chế Tool Retrieval (ví dụ dùng Vector DB). Khi hệ thống mở rộng lên hàng chục tools (giá vàng, tỷ giá ngoại tệ, chứng khoán...), thay vì nhồi nhét toàn bộ description vào System Prompt làm tốn kém Prompt Tokens, hệ thống sẽ tự động tìm và chỉ inject những tools liên quan đến câu hỏi hiện tại.


  # Repo nhóm
  ## Link: [!https://github.com/FWD-LeTung/ReAct-Agent.git]