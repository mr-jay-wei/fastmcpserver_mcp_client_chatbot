# conda env mcp_env ,Python版本 3.10.18
# 关闭 proxy
# 使用方法：用python 把server启动
from datetime import datetime
import requests
from fastmcp import FastMCP

mcp = FastMCP("weather")


@mcp.tool()
def get_today():
    """获取今天的日期。

    Returns:
        str: 当前的日期字符串，格式为 'YYYY.MM.DD'。
    """
    return datetime.today().strftime('%Y.%m.%d')


@mcp.tool()
def get_weather(city: str, date: str):
    """获取指定城市在特定日期的天气情况。

    Args:
        city (str): 需要查询天气的城市名称，例如 "北京" 或 "London"。
        date (str): 需要查询的日期，可以使用 "今天"、"明天" 等相对描述，或 "2023.10.27" 这样的具体日期。

    Returns:
        str: 包含该城市天气情况描述的原始文本。
    """
    endpoint = "https://wttr.in"

    response = requests.get(f"{endpoint}/{city}")
    return response.text


if __name__ == '__main__':
    mcp.run('sse', host='0.0.0.0', port=8000, path='/toolmcp')
