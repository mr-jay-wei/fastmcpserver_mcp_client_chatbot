# conda env mcp_env ,Python版本 3.10.18
# 关闭 proxy
# 使用方法：先把server启动，然后启动chat_bot.py  : python chat_bot.py http://127.0.0.1:8082/sse

import asyncio
import json
from typing import Optional
from contextlib import AsyncExitStack
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())
import os

from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPClient:
    def __init__(self):
        """初始化MCP客户端"""
        self.exit_stack = AsyncExitStack()
        self.openai_api_key = os.getenv("DASHSCOPE_API_KEY")  # 调用模型的api_key
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 调用模型url, 这里以QwQ-32B作演示
        self.model = "qwen-turbo"  # 调用QwQ-32B模型
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None  # Optional提醒用户该属性是可选的，可能为None

    async def connect_to_sse_server(self, server_url):
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
        """使用大模型处理查询并调用MCP Server可用的MCP工具"""
        messages = [{"role": "user", "content": query}]
        response = await self.session.list_tools()
        
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
            }
            for tool in response.tools
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools
        )

        # 处理返回内容
        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            # 返回结果是使用工具的建议, 就解析并调用工具
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            # 假设 json 已被 import
            tool_args = json.loads(tool_call.function.arguments)
            
            # 执行工具
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")
            result = await self.session.call_tool(tool_name, tool_args)
            
            # 将模型返回的调用工具的对话记录保存在messages中
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text, # 假设 result 的结构如此
                "tool_call_id": tool_call.id,
            })

            # 将上面的结果返回给大模型用于生产最终结果
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        else :       
            return content.message.content

    async def chat_loop(self):
        """运行交互式聊天"""
        print("\n MCP客户端已启动[输入quit退出]")

        while True:
            try:
                # 注意: input() 是一个阻塞操作
                query = input("\n用户: ").strip()
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print(f"\nllm: {response}") # 注意: 这里硬编码了模型名称
            except Exception as e:
                print(f"发生错误: {str(e)}")

    async def clean(self):
        """清理资源"""
        await self.exit_stack.aclose()

async def main():
    print("abc") # 这看起来是一个临时的调试打印语句
    if len(sys.argv) < 2:
        print("使用方法是: python client.py server_url")#python chat_bot.py http://127.0.0.1:8082/sse
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.clean()

if __name__ == "__main__":
    # 将 import 语句放在文件顶部是更好的实践
    import sys
    asyncio.run(main())