import os
import re
import json 
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        IMPORTANT RULES:
        1. After you output an 'Action', you MUST STOP and wait for an 'Observation'. 
        2. NEVER guess or hallucinate the result of an Action. 
        3. NEVER write the 'Observation' yourself. The system will provide it to you.
        4. Each step should only contain ONE Thought and ONE Action.
        5. NẾU người dùng hỏi chung chung về lãi suất các ngân hàng mà không nhắc đến tên ngân hàng cụ thể, BẮT BUỘC dùng Action với tham số bank_name="all". 
        6. NẾU người dùng không chỉ định loại lãi suất, BẮT BUỘC dùng type_rate="all" thay vì hỏi lại.

        Use the following format strictly:
        Question: the input question you must answer
        Thought: your line of reasoning.
        Action: tool_name({{"arg1": "value1"}})
        (Wait for Observation here)
        Final Answer: your final response to the user.
        """

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # 1. Thêm câu hỏi của user vào lịch sử
        self.history.append(f"User: {user_input}")
        
        # 2. Xây dựng context từ lịch sử hội thoại (Lấy 5-6 lượt gần nhất để khỏi tràn token)
        history_str = "\n".join(self.history[-6:])
        
        # 3. Gắn lịch sử vào Prompt hiện tại
        current_prompt = f"Chat History:\n{history_str}\n\nQuestion: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            print(f"--- Bước {steps + 1} ---")
            
            # Gọi LLM
            response_dict = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            result = response_dict["content"]
            print(f"LLM Output:\n{result}\n")
            
            current_prompt += f"{result}\n"
            
            final_answer_match = re.search(r'Final Answer:(.*)', result, re.IGNORECASE | re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                
                # 4. LƯU LẠI câu trả lời của Agent vào lịch sử trước khi trả về kết quả
                self.history.append(f"Assistant: {final_answer}")
                return final_answer
            
            action_match = re.search(r'Action:\s*([a-zA-Z0-9_]+)\((.*?)\)', result, re.IGNORECASE)
            
            if action_match:
                tool_name = action_match.group(1).strip()
                args_str = action_match.group(2).strip()
                
                observation = self._execute_tool(tool_name, args_str)
                print(f"Observation: {observation}\n")
                
                current_prompt += f"Observation: {observation}\n"
            else:
                current_prompt += "Observation: Lỗi format. Hãy đưa ra 'Action:' hoặc 'Final Answer:'.\n"
            
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        fail_msg = "Xin lỗi, tôi đã suy nghĩ quá lâu (vượt giới hạn số bước) mà chưa tìm ra câu trả lời."
        self.history.append(f"Assistant: {fail_msg}")
        return fail_msg
    
    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Helper method to execute tools by name.
        """

        for tool in self.tools:
            if tool['name'] == tool_name:
                
                # Lấy ra hàm (function) thực tế bằng Python đã được map trong dict
                func = tool.get('function')
                if not func:
                    return f"Lỗi: Công cụ '{tool_name}' không được cấu hình hàm thực thi (key 'function')."
                
                try:
                    # Ép kiểu chuỗi arguments (từ LLM) thành Dictionary
                    args_dict = {}
                    if args_str:
                        args_dict = json.loads(args_str)
                    
                    result = func(**args_dict)
                    return str(result)
                    
                except json.JSONDecodeError:
                    return f"Lỗi Observation: Cú pháp tham số không hợp lệ. Tham số phải là chuẩn JSON. Bạn (LLM) đã truyền: {args_str}"
                except Exception as e:
                    return f"Lỗi Observation trong khi chạy tool: {str(e)}"
                f
        return f"Observation: Tool '{tool_name}' không tồn tại. Vui lòng kiểm tra lại tên tool."