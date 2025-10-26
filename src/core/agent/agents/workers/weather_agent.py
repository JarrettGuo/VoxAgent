#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import WEATHER_AGENT_PROMPT


class WeatherAgent(
    BaseAgent,
    agent_type="weather",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["gaode_weather"],
):
    """天气 Agent"""

    agent_name = "weather_agent"
    agent_description = (
        "负责中国大陆的天气信息的查询"
        "适用场景：查天气预报等"
        "这个 Agent 只适用查询国内城市的天气信息，不支持国际城市。"
    )
    agent_system_prompt = """你是一个天气信息专家。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = WEATHER_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
