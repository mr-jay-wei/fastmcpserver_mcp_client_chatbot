from fastmcp import FastMCP
mcp = FastMCP(debug = True)

from datetime import datetime
import requests

@mcp.tool()
def calculate_bmi(weight_kg:float,height_m:float)->float:
	'''
	通过给定的体重和身高计算BMI指数。
	'''
	return weight_kg / (height_m ** 2)

@mcp.tool()
def get_today():
    """
    获取今天的日期
    :return: 年月日的字符串
    """
    return datetime.today().strftime('%Y.%m.%d')


@mcp.tool()
def get_weather(city: str, date: str):
    """
    获取 city 的天气情况
    :param city: 城市
    :param date: 日期
    :return: 城市天气情况的描述
    """
    endpoint = "https://wttr.in"

    response = requests.get(f"{endpoint}/{city}")
    return response.text


if __name__ == '__main__':
	mcp.run("sse",host = "0.0.0.0",port = 8082)