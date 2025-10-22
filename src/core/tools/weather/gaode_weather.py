from typing import Any, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import Field  # 添加 Field 导入

from src.core.tools.base.schemas import GaodeWeatherSchema
from src.utils.logger import logger


class GaodeWeatherTool(BaseTool):
    """高德天气查询工具 - 查询中国城市的天气预报"""

    name: str = "gaode_weather"
    description: str = (
        "用于查询中国城市的天气预报。支持查询当前天气、未来几天的天气预报等信息。"
        "输入城市名称（如：北京、上海、广州），返回详细的天气信息。"
    )
    args_schema: Type[GaodeWeatherSchema] = GaodeWeatherSchema

    api_key: str = Field(default="", description="高德天气 API Key")

    def __init__(self, api_key: str = None, **kwargs):
        """初始化高德天气工具"""
        if api_key is None:
            api_key = ""

        super().__init__(api_key=api_key, **kwargs)

        if not self.api_key:
            logger.warning("API Key not provided. Please set the GAODE_API_KEY environment variable.")

    def _run(self, city: str, **kwargs: Any) -> str:
        """执行天气查询"""
        try:
            api_domain = "https://restapi.amap.com/v3"
            session = requests.Session()

            # 1. 查询城市的行政区域编码（adcode）
            city_response = session.get(
                f"{api_domain}/config/district",
                params={
                    "key": self.api_key,
                    "keywords": city,
                    "subdistrict": 0,
                },
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10,
            )
            city_response.raise_for_status()
            city_data = city_response.json()

            # 检查城市查询结果
            if city_data.get("info") != "OK" or not city_data.get("districts"):
                return f"Don't find city: {city}"

            ad_code = city_data["districts"][0]["adcode"]

            # 2. 查询天气预报
            weather_response = session.get(
                f"{api_domain}/weather/weatherInfo",
                params={
                    "key": self.api_key,
                    "city": ad_code,
                    "extensions": "all",  # 获取预报天气
                },
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10,
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # 检查天气查询结果
            if weather_data.get("info") != "OK":
                return f"Get weather info failed for city: {city}"

            # 3. 格式化输出
            formatted_result = self._format_weather_data(city, weather_data)

            return formatted_result

        except requests.exceptions.Timeout:
            error_msg = f"Timeout when querying weather for city: {city}"
            logger.error(error_msg)
            return error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"Internet error when querying weather for city {city}: {str(e)}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to get weather for city {city}: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _format_weather_data(self, city: str, weather_data: dict) -> str:
        """格式化天气数据"""
        try:
            forecasts = weather_data.get("forecasts", [])
            if not forecasts:
                return f"Failed to get weather forecast for city: {city}"

            forecast = forecasts[0]
            city_name = forecast.get("city", city)
            casts = forecast.get("casts", [])

            if not casts:
                return f"{city_name}：There is no weather forecast available."

            # 格式化输出
            result = [f"{city_name} Weather Forecast:\n"]

            for cast in casts[:3]:  # 只显示前3天
                date = cast.get("date", "未知日期")
                week = cast.get("week", "")
                dayweather = cast.get("dayweather", "未知")
                nightweather = cast.get("nightweather", "未知")
                daytemp = cast.get("daytemp", "?")
                nighttemp = cast.get("nighttemp", "?")
                daywind = cast.get("daywind", "")
                daypower = cast.get("daypower", "")

                result.append(
                    f"{date} week{week}\n"
                    f"Day：{dayweather} {daytemp}℃ {daywind}{daypower}\n"
                    f"Night：{nightweather} {nighttemp}℃\n"
                )

            return "".join(result)

        except Exception as e:
            logger.error(f"Error formatting weather data for city {city}: {str(e)}")
            return f"Error formatting weather data for city {city}."


def gaode_weather(api_key: str = None, **kwargs) -> BaseTool:
    """工厂函数：创建高德天气查询工具"""
    try:
        tool = GaodeWeatherTool(api_key=api_key, **kwargs)
        return tool

    except Exception as e:
        logger.error(f"Failed to create GaodeWeatherTool: {e}")
        raise
