'''
conda env mcp_env ,Python版本 3.10.18
关闭 proxy
使用方法：先把server启动，然后启动chat_bot.py  : python chat_bot.py http://127.0.0.1:8083/my-custom-path

MCP客户端 - 专注于list_tools() 和 call_tool() 两个核心方法
再集成llm智能理解工具功能和参数返回具体使用参数
'''

import asyncio
import json
import sys

from typing import List,Dict,Any,Optional
from openai import OpenAI
# 加载环境变量
import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

from fastmcp import Client


from pydantic import BaseModel
# 请求/响应模型
class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    result: str
    success: bool
    error: Optional[str] = None

class ToolsResponse(BaseModel):
    tools: List[Dict[str, Any]]
    count: int


class MCPClient:
    def __init__(self, mcpserver_url: str):
        self.openai_api_key = os.getenv("KIMI_API_KEY")  # 调用模型的api_key
        self.base_url = "https://api.moonshot.cn/v1"  # 调用模型url
        self.model = "kimi-k2-0711-preview"  # 调用模型
        self.llm = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        self.mcpserver_url = mcpserver_url
        self.conversation_history = [] # 新增一个列表来存储历史

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        async with Client(self.mcpserver_url) as client:
            tool_list_response = await client.list_tools()
        # print(f"tool_list_response:\n {tool_list_response}")
        available_tools = [
			{
				"type": "function",
				"function": {
					"name": tool.name,
					"description": tool.description,
					"input_schema": tool.inputSchema
				}
			}
			for tool in tool_list_response]

        # print(f"\n已连接到服务器 (使用Streamable HTTP)，支持以下工具:", [tool.name for tool in tool_list_response])
        
        return available_tools


    async def process_query(self, query: str, available_tools: List) -> str:
        """
        使用大模型处理查询，并支持多轮自主工具调用，直到任务完成。
        """
        system_prompt = (
            "你是一个名为'MCP智能助手'的AI。你的核心任务是准确地回答用户问题。"
            "你的行为准则如下：\n"
            "1. **优先使用工具**：对于任何涉及实时数据（如日期、天气）、计算（如BMI）或其他专业功能的问题，你必须优先调用相应的工具来获取最准确的信息。\n"
            "2. **严禁捏造**：绝对不允许在没有可靠数据来源的情况下编造事实，特别是日期、天气、计算结果等。\n"
            "3. **严禁向用户提问**：你绝对不允许询问用户任何问题。你需要自己分析所有的信息做出决策。\n"
            "4. **多任务处理**：如果用户一次提出多个请求，你必须逐一处理。你一次只调用一个工具，在完成一个工具调用后，你需要回顾用户的完整请求，检查是否还有未完成的部分，并继续调用其他所需工具，直到所有任务都解决。\n"
            "5. **总结汇报**：在所有工具调用完成后，将结果整合起来，给用户一个清晰、完整、流畅的最终答复。"
        )
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": query})


        while True:
            
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=available_tools
            )
            response_message = response.choices[0].message
            messages.append(response_message.model_dump())

            if response.choices[0].finish_reason == "tool_calls":
                print(f"\n[LLM决定调用工具...]")
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    print(f"[正在调用工具: {tool_name}，参数: {tool_args}]")
                    async with Client(self.mcpserver_url) as client:
                        result = await client.call_tool(tool_name, tool_args)
                    # print(f"tool_call_result:\n {result}")
                    tool_output = result.content[0].text
                    print(f"[工具返回结果: {tool_output[:200]}...]")
                    messages.append(
                        {"role": "tool", 
                          "content": tool_output, 
                          "tool_call_id": tool_call.id})
                continue
            else:
                print(f"\n[LLM认为任务完成，生成最终回答]")
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": response_message.content})
                return response_message.content

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\n===== MCP 客户端已启动 (输入 'quit' 退出) =====")
        while True:
            try:
                query = input("\n用户: ").strip()
                if query.lower() == 'quit':
                    print("正在退出...")
                    break
                available_tools = await self.get_mcp_tools()
                response = await self.process_query(query, available_tools)
                print(f"\n助手: {response}")
            except Exception as e:
                print(f"发生错误: {str(e)}")

async def main():
    if len(sys.argv) < 2:
        # 3. 修改使用说明和示例URL
        print("使用方法: python chat_bot.py <server_url>")
        print("例如 (Streamable HTTP): python chat_bot.py http://127.0.0.1:8083/my-custom-path")
        sys.exit(1)

    client = MCPClient(sys.argv[1])
    try:
        await client.chat_loop()
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())