# conda env mcp_env ,Python版本 3.10.18
# 关闭 proxy
# 使用方法：先把server启动，然后启动chat_bot.py  : python chat_bot.py http://127.0.0.1:8082/sse

import asyncio
import json
import sys
import os
from typing import Optional
from contextlib import AsyncExitStack

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

from mcp import ClientSession
from mcp.client.sse import sse_client

# 加载环境变量
_ = load_dotenv(find_dotenv())

class MCPClient:
    def __init__(self):
        """初始化MCP客户端"""
        self.exit_stack = AsyncExitStack()
        self.openai_api_key = os.getenv("KIMI_API_KEY")  # 调用模型的api_key
        self.base_url = "https://api.moonshot.cn/v1"  # 调用模型url
        self.model = "kimi-k2-0711-preview"  # 调用模型
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None  # Optional提醒用户该属性是可选的，可能为None

    async def connect_to_sse_server(self, server_url):
        """连接到MCP服务器并初始化会话"""
        # 连接sse服务端，因为是基于http协议的，需要传入url
        sse_transport = await self.exit_stack.enter_async_context(sse_client(server_url))
        self.write, self.read = sse_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.write, self.read))
        await self.session.initialize()  # 与服务器建立sse连接
        
        # 列出MCP服务器上的工具
        response = await self.session.list_tools()
        tools = response.tools
        print(f"\n已连接到服务器，支持以下工具:", [tool.name for tool in tools]) # 打印服务端可用的工具

    async def process_query(self, query: str) -> str:
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
            {"role": "system", "content": system_prompt}, # 添加系统提示
            {"role": "user", "content": query}
        ]
        
        # 从服务器获取可用工具的描述
        tool_list_response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
            }
            for tool in tool_list_response.tools
        ]

        # 循环与LLM交互，直到它提供最终答案而不是工具调用
        while True:
            # 向LLM发送当前对话历史和可用工具
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=available_tools
            )

            response_message = response.choices[0].message
            # 必须将模型的回复（即使是工具调用请求）也添加到历史中
            messages.append(response_message.model_dump())

            # 检查LLM是否要求调用工具
            if response.choices[0].finish_reason == "tool_calls":
                print(f"\n[LLM决定调用工具...]")
                # 遍历所有被请求的工具调用
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # 执行工具
                    print(f"[正在调用工具: {tool_name}，参数: {tool_args}]")
                    result = await self.session.call_tool(tool_name, tool_args)
                    tool_output = result.content[0].text
                    print(f"[工具返回结果: {tool_output[:100]}...]") # 打印部分结果以防过长
                    
                    # 将工具执行结果添加到对话历史中，以便LLM进行下一步决策
                    messages.append({
                        "role": "tool",
                        "content": tool_output,
                        "tool_call_id": tool_call.id,
                    })
                # 继续下一次循环，让LLM根据工具结果进行下一步操作
                continue
            else:
                # 如果LLM没有要求调用工具，说明它已经生成了最终答案
                print(f"\n[LLM认为任务完成，生成最终回答]")
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
                
                # 开始处理查询
                response = await self.process_query(query)
                print(f"\n助手: {response}")
            except Exception as e:
                print(f"发生错误: {str(e)}")

    async def clean(self):
        """清理资源"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("使用方法: python chat_bot.py <server_url>")
        print("例如: python chat_bot.py http://127.0.0.1:8082/sse")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.clean()

if __name__ == "__main__":
    asyncio.run(main())