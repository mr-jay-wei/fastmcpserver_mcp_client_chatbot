"""
conda env mcp_env ,Python版本 3.10.18
关闭 proxy
使用方法：先把server启动，然后启动simple_mcp_client.py,观察mcp client返回的数据结构和集成了mcp client的函数返回的数据结构
 
简化的MCP客户端 - 专注于核心功能
提供 list_tools() 和 call_tool() 两个核心方法，供其他项目集成使用
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastmcp import Client


class SimpleMCPClient:
    """
    简化的MCP客户端类
    
    核心功能：
    1. list_tools() - 获取服务器提供的所有工具及其描述
    2. call_tool() - 调用指定工具并返回结果
    
    使用示例：
        client = SimpleMCPClient("http://127.0.0.1:8083/my-custom-path")
        tools = await client.list_tools()
        result = await client.call_tool("get_weather", {"city": "北京", "date": "今天"})
    """
    
    def __init__(self, server_url: str):
        """
        初始化MCP客户端
        
        Args:
            server_url: MCP服务器的URL地址
        """
        self.server_url = server_url
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取服务器提供的所有工具列表
        
        Returns:
            工具列表，每个工具包含：
            - name: 工具名称
            - description: 工具描述
            - parameters: 工具参数schema
        """
        async with Client(self.server_url) as client:
            tool_list_response = await client.list_tools()
        print(f"tool_list_response:\n {tool_list_response}")
        '''
        tool_list_response:
        [Tool(
            name = 'calculate_bmi', 
            title = None, 
            description = '通过给定的体重和身高计算BMI指数。\n\nArgs:xxxx', 
            inputSchema = {
                    'properties': {
                        'weight_kg': {
                            'title': 'Weight Kg',
                            'type': 'number'
                            },
                        'height_m': {
                            'title': 'Height M',
                            'type': 'number'
                            }
                        },
                    'required': ['weight_kg', 'height_m'],
                    'type': 'object'
                    }, 
            outputSchema = {
                    'properties': {
                        'result': {
                            'title': 'Result',
                            'type': 'number'
                            }
                        },
                    'required': ['result'],
                    'title': '_WrappedResult',
                    'type': 'object',
                    'x-fastmcp-wrap-result': True
                    }, 
            annotations = None, 
            meta = None
        )]
        '''
        tools = []
        for tool in tool_list_response:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })
        
        return tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用指定的工具
        
        Args:
            tool_name: 要调用的工具名称
            arguments: 工具参数
            
        Returns:
            包含调用结果的字典：
            - success: 是否成功
            - result: 工具返回的结果
            - error: 错误信息（如果有）
        """
        try:
            async with Client(self.server_url) as client:
                result = await client.call_tool(tool_name, arguments)
            print(f"tool_call_result:\n {result}")
            '''
            tool_call_result:
            CallToolResult(
                content=[TextContent(type='text', text='2025-07-15 17:34:06', annotations=None, meta=None)], 
                structured_content={'result': '2025-07-15 17:34:06'}, 
                data='2025-07-15 17:34:06', 
                is_error=False
                )
            '''
            return {
                "success": True,
                "result": result.content[0].text,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }
    

# 使用示例
async def example_usage():
    """使用示例"""
    client = SimpleMCPClient("http://127.0.0.1:8083/my-custom-path")
    
    # 1. 获取工具列表
    print("=== 获取工具列表 ===")
    tools = await client.list_tools()
    print(f"function tools:\n {tools}")
    '''
    打印结果：
    [{
        'name': 'calculate_bmi',
        'description': '通过给定的体重和身高计算BMI指数。\n\nArgs:\n    weight_kg (float): 用户的体重，单位为公斤(kg)。\n    height_m (float): 用户的身高，单位为米(m)。\n\nReturns:\n    float: 计算得出的BMI指数值。',
        'parameters': {
            'properties': {
                'weight_kg': {
                    'title': 'Weight Kg',
                    'type': 'number'
                    },
                'height_m': {
                    'title': 'Height M',
                    'type': 'number'
                    }
                },
            'required': ['weight_kg', 'height_m'],
            'type': 'object'
            }
    }]
    '''
    # 2. 调用工具
    print("\n=== 调用工具示例 ===")
    
    # 获取当前时间
    result = await client.call_tool("get_current_time", {})
    print(f"当前时间:\n {result}")
    # {'success': True, 'result': '2025-07-15 17:17:16', 'error': None}
    # 计算BMI
    result = await client.call_tool("calculate_bmi", {"weight_kg": 70, "height_m": 1.75})
    print(f"BMI计算结果:\n {result}")
    
    # 获取天气
    #result = await client.call_tool("get_weather", {"city": "北京", "date": "今天"})
    #print(f"天气查询结果:\n {result}")


if __name__ == "__main__":
    asyncio.run(example_usage())