#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import SEARCH_AGENT_PROMPT


class SearchAgent(
    BaseAgent,
    agent_type="search",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["wikipedia_search", "duckduckgo_search", "google_serper"],
):
    """浏览器操作 Agent"""

    agent_name = "browser_agent"
    agent_description = (
        "负责网络信息检索和知识查询，包括：通过搜索引擎查找实时信息。"
        "当其他工具无法搜索天气信息时，可使用该 Agent 进行天气的查询。"
        "在维基百科查询百科知识、获取新闻资讯、查找技术文档等。"
        "适用场景：搜索教程、了解概念定义、获取最新资讯、查询国外天气状况等"
    )
    agent_system_prompt = """你是一个信息检索专家。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = SEARCH_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
