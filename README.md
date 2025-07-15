# 简化MCP客户端

这个项目提供了一个简化的MCP（Model Context Protocol）客户端实现，专注于核心功能，方便其他项目集成。

## 核心理念

正如你所说，一个MCP客户端最核心的就是两个方法：
- `list_tools()` - 获取服务器提供的工具列表及其功能描述
- `call_tool()` - 调用指定工具并获取结果

剩下的就是用户根据自己的需求来使用这些工具。

## 项目结构

```
├── simple_mcp_client.py          # 核心客户端类
├── fastmcp_server_streamhttp.py  # 示例MCP服务器
├── fastmcp_client_streamhttp_chatbot.py  # 完整聊天机器人示例
└── requirements.txt               # 依赖包
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 进入环境mcp_env, Python版本3.10.18，启动MCP服务器

```bash
python fastmcp_server_streamhttp.py
```

服务器将在 `http://127.0.0.1:8083/my-custom-path` 启动

### 3. 使用简化客户端

```python
from simple_mcp_client import SimpleMCPClient
import asyncio

async def main():
    # 创建客户端
    client = SimpleMCPClient("http://127.0.0.1:8083/my-custom-path")
    
    # 获取工具列表
    tools = await client.list_tools()
    print("可用工具:", [tool['name'] for tool in tools])
    
    # 调用工具
    result = await client.call_tool("get_current_time", {})
    print("当前时间:", result['result'])
    
    # 计算BMI
    result = await client.call_tool("calculate_bmi", {
        "weight_kg": 70, 
        "height_m": 1.75
    })
    print("BMI:", result['result'])

asyncio.run(main())
```

## API 文档

### SimpleMCPClient

#### `__init__(server_url: str)`
初始化客户端
- `server_url`: MCP服务器的URL地址

#### `async list_tools() -> List[Dict[str, Any]]`
获取服务器提供的所有工具列表

返回格式：
```python
[
    {
        "name": "tool_name",
        "description": "工具描述",
        "parameters": {...}  # JSON Schema格式的参数定义
    }
]
```

#### `async call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]`
调用指定工具

参数：
- `tool_name`: 工具名称
- `arguments`: 工具参数字典

返回格式：
```python
{
    "success": True/False,
    "result": "工具返回结果",
    "error": "错误信息（如果有）"
}
```

#### `async get_openai_tools_format() -> List[Dict[str, Any]]`
获取OpenAI格式的工具定义，用于与LLM集成

## 集成示例

### 基础集成

```python
from simple_mcp_client import SimpleMCPClient

class MyApp:
    def __init__(self):
        self.mcp = SimpleMCPClient("http://127.0.0.1:8083/my-custom-path")
    
    async def init(self):
        self.tools = await self.mcp.list_tools()
    
    async def use_tool(self, name, params):
        return await self.mcp.call_tool(name, params)
```

### 与LLM集成

```python
from openai import OpenAI
from simple_mcp_client import SimpleMCPClient

class LLMWithTools:
    def __init__(self):
        self.llm = OpenAI()
        self.mcp = SimpleMCPClient("http://127.0.0.1:8083/my-custom-path")
    
    async def chat(self, message):
        # 获取工具定义
        tools = await self.mcp.get_openai_tools_format()
        
        # 调用LLM
        response = self.llm.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            tools=tools
        )
        
        # 处理工具调用
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                result = await self.mcp.call_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                # 处理结果...
```

## 运行示例

### 1. 运行基础示例
```bash
python simple_mcp_client.py
```

### 2. 运行完整聊天机器人
```bash
python fastmcp_client_streamhttp_chatbot.py http://127.0.0.1:8083/my-custom-path
```

## 服务器提供的工具

当前示例服务器提供以下工具：

1. **get_current_time** - 获取当前时间
2. **calculate_bmi** - 计算BMI指数
   - 参数：weight_kg (float), height_m (float)
3. **get_weather** - 获取天气信息
   - 参数：city (str), date (str)

## 扩展使用

这个简化的客户端设计为通用组件，你可以：

1. **集成到现有项目** - 只需要导入 `SimpleMCPClient` 类
2. **自定义工具处理** - 根据 `list_tools()` 的结果实现自己的工具调用逻辑
3. **与任何LLM集成** - 使用 `get_openai_tools_format()` 获取标准格式的工具定义
```python
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

response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=available_tools
            )
```

4. **构建专业应用** - 基于这两个核心方法构建复杂的应用逻辑

## 设计原则

- **简单性** - 只提供最核心的功能
- **通用性** - 不绑定特定的使用场景
- **可扩展性** - 易于在其他项目中集成和扩展
- **标准兼容** - 支持OpenAI工具格式等标准

这样的设计让你可以专注于业务逻辑，而不用关心MCP协议的底层细节。