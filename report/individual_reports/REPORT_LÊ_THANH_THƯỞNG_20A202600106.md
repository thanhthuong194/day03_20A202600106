# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Thanh Thưởng
- **Student ID**: 20A202600106
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)

*Trong bài lab số 3 này, mình đã tham gia triển khai các module cốt lõi của ReAct Agent System bao gồm: **agent.py** (chứa logic vòng lặp ReAct và xử lý công cụ), **calculate.py** (công cụ tính toán tiền lãi tiết kiệm), và **main.py** (giao diện chatbot tương tác với người dùng).*

### 1. Module: src/agent/agent.py
- **Code Highlights**: Toàn bộ class `ReActAgent` với hai hàm chính:
  - `get_system_prompt()` (lines 20-40): Xây dựng system prompt định nghĩa cách Agent hoạt động theo framework ReAct (Thought-Action-Observation-Answer)
  - `run()` (lines 42-112): Triển khai vòng lặp chính của Agent với các tính năng:
    - Quản lý chat history để duy trì ngữ cảnh hội thoại
    - Theo dõi và cộng dồn metrics (prompt_tokens, completion_tokens, latency) qua các bước
    - Parse response từ LLM để tách Thought, Action, và Final Answer
    - Gọi công cụ thông qua `_execute_tool()` và trả về Observation
    - Xử lý trường hợp vượt quá giới hạn bước (max_steps)
  - `_execute_tool()` (lines 114-141): Thực thi công cụ với xử lý lỗi JSON và runtime exceptions

- **Documentation**: 
  - Agent được thiết kế theo mẫu **ReAct Pattern** (Reasoning + Acting), cho phép LLM suy luận từng bước trước khi quyết định gọi tool hoặc đưa ra câu trả lời cuối cùng
  - System prompt được tối ưu với các quy tắc quan trọng:
    - Bắt buộc LLM phải chờ Observation sau mỗi Action (tránh hallucination)
    - Yêu cầu sử dụng `bank_name="all"` khi người dùng hỏi chung chung về lãi suất
    - Tự động điền `type_rate="all"` khi không được chỉ định
  - Hỗ trợ logging telemetry toàn diện với sự kiện AGENT_START và AGENT_END để theo dõi hiệu năng và chi phí

### 2. Module: src/tools/calculate.py
- **Code Highlights**: Hàm `calculate_savings_interest()` (lines 3-47) và tool specification (lines 52-60)

- **Documentation**:
  - **Chức năng**: Tính toán chính xác tiền lãi tiết kiệm ngân hàng theo công thức lãi đơn cuối kỳ: `Lãi = Gốc × (Lãi suất/100) × (Số tháng/12)`
  - **Input validation**: Kiểm tra tính hợp lệ của dữ liệu (số tiền dương, lãi suất không âm, kỳ hạn > 0)
  - **Error handling**: Xử lý các lỗi ValueError (sai định dạng số) và Exception tổng quát
  - **Output format**: Trả về báo cáo chi tiết với format tiền tệ Việt Nam (dấu chấm phân cách hàng nghìn), bao gồm:
    - Tiền gốc
    - Lãi suất áp dụng
    - Kỳ hạn gửi
    - Tiền lãi sinh ra
    - Tổng tiền nhận cuối kỳ (Gốc + Lãi)
  - **Tool spec**: Cấu hình tool description rõ ràng giúp LLM hiểu cách sử dụng đúng các tham số (principal, rate_percent, months)

### 3. Module: main.py
- **Code Highlights**: Toàn bộ file (lines 1-67) với hàm `main()` (lines 8-64)

- **Documentation**:
  - **Khởi tạo hệ thống**: 
    - Tạo OpenAI provider với model `gpt-4o` (model mạnh để đảm bảo chất lượng reasoning)
    - Đăng ký danh sách tools cho Agent (`fetch_interest_rates` và `calculate_savings_interest`)
    - Khởi tạo ReActAgent với `max_steps=10`
  - **Vòng lặp chatbot**:
    - Giao diện thân thiện với emoji và hướng dẫn sử dụng
    - Xử lý lệnh thoát (exit/quit/thoát/bye)
    - Try-except toàn diện để catch KeyboardInterrupt và các lỗi runtime
    - Hiển thị kết quả rõ ràng với đường phân cách (separator)
  - **User Experience**: Tạo trải nghiệm chat tự nhiên với thông báo "Agent đang suy nghĩ..." trong khi xử lý 
---

## II. Debugging Case Study (10 Points)

### Bug 1: Vòng lặp vô hạn (Infinite Loop) do LLM không output đúng format
- **Problem Description**: Agent liên tục lặp lại các bước mà không đưa ra được Final Answer, tiêu tốn token và thời gian. LLM đôi khi sinh ra text không tuân thủ format "Thought-Action-Observation-Final Answer" được quy định trong system prompt, dẫn đến việc regex không match được, Agent phải retry liên tục.

- **Log Source**: 
  ```
  --- Bước 8 ---
  LLM Output:
  Thought: Tôi cần lấy lãi suất...
  Hãy sử dụng công cụ fetch_interest_rates
  
  Observation: Lỗi format. Hãy đưa ra 'Action:' hoặc 'Final Answer:'.
  --- Bước 9 ---
  (Lặp lại tương tự)
  ```

- **Diagnosis**: 
  - **Nguyên nhân từ Model**: Sử dụng model yếu hơn (như gpt-4o-mini) dẫn đến khả năng instruction-following kém, đặc biệt với các format phức tạp
  - **Nguyên nhân từ Prompt**: System prompt chưa đủ rõ ràng về việc BẮT BUỘC phải tuân thủ format `Action: tool_name({"param": "value"})`
  - **Nguyên nhân từ Code**: Không có cơ chế fallback khi LLM fail liên tục, chỉ dựa vào max_steps để thoát

- **Solution**:
  1. **Nâng cấp model**: Đổi từ `gpt-4o-mini` sang `gpt-4o` trong main.py (line 10) để cải thiện reasoning capability
  2. **Cải thiện prompt**: Bổ sung quy tắc cụ thể hơn trong `get_system_prompt()`:
     ```python
     # Line 34-36 in agent.py
     Use the following format strictly:
     Question: the input question you must answer
     Thought: your line of reasoning.
     Action: tool_name({"arg1": "value1"})  # Phải đúng syntax này
     (Wait for Observation here)
     Final Answer: your final response to the user.
     ```
  3. **Thêm error message chi tiết**: Khi regex không match (line 97), trả về Observation hướng dẫn LLM fix format

### Bug 2: Agent gọi tool với tham số không hợp lệ
- **Problem Description**: LLM truyền tham số sai định dạng hoặc thiếu tham số bắt buộc, gây crash tool hoặc trả về kết quả sai. Ví dụ: truyền `principal="200 triệu"` (chuỗi có chữ) thay vì `principal=200000000` (số).

- **Log Source**:
  ```
  Action: calculate_savings_interest({"principal": "200 triệu", "rate_percent": "4.6%", "months": "12 tháng"})
  Observation: Lỗi: Agent truyền sai định dạng dữ liệu. Yêu cầu truyền số thuần túy...
  ```

- **Diagnosis**:
  - **Root cause**: LLM có xu hướng sinh ra human-friendly format (ví dụ: "200 triệu", "4.6%") thay vì machine-readable format (200000000, 4.6)
  - **Thiếu type coercion**: Ban đầu hàm `calculate_savings_interest()` không có ép kiểu, nhận trực tiếp tham số từ LLM
  - **Tool description chưa rõ**: Mô tả tool không nhấn mạnh việc "chỉ truyền số, không chữ"

- **Solution**:
  1. **Type coercion trong tool** (lines 16-19 của calculate.py):
     ```python
     principal = float(principal)  # Ép kiểu để phòng trường hợp LLM truyền nhầm string
     rate_percent = float(rate_percent)
     months = int(months)
     ```
  2. **Cải thiện tool description** trong main.py (line 22):
     ```python
     "description": "Tính tiền lãi. Tham số: principal (float - CHỈ NHẬP SỐ), 
                     rate_percent (float - CHỈ NHẬP SỐ), months (int)."
     ```
  3. **Validation và error message rõ ràng** (lines 21-22, 44-47):
     - Kiểm tra giá trị âm/bằng 0
     - Trả về message chi tiết giúp Agent tự correct trong vòng lặp tiếp theo
     - Try-catch ValueError để xử lý trường hợp không ép kiểu được

### Bug 3: Chat history bị quên (Context loss) trong multi-turn conversation
- **Problem Description**: Sau vài câu hỏi liên tiếp, Agent "quên" ngữ cảnh cuộc hội thoại trước đó, phải hỏi lại thông tin người dùng đã cung cấp.

- **Diagnosis**: 
  - Ban đầu hàm `run()` không lưu chat history, mỗi lần gọi là một prompt hoàn toàn mới
  - LLM không có thông tin về các câu hỏi/trả lời trước đó

- **Solution** (lines 45-48 trong agent.py):
  ```python
  self.history.append(f"User: {user_input}")
  history_str = "\n".join(self.history[-6:])  # Chỉ lấy 6 message gần nhất (tiết kiệm token)
  current_prompt = f"Chat History:\n{history_str}\n\nQuestion: {user_input}\n"
  ```
  - Lưu history vào `self.history` (khởi tạo ở line 18)
  - Khi có Final Answer, lưu luôn response của Agent (line 86): `self.history.append(f"Assistant: {final_answer}")`
  - Giới hạn 6 message cuối để cân bằng giữa context và cost


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
  ## Link: [https://github.com/thanhthuong194/day03_20A202600106]