#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import IMAGE_GEN_AGENT_PROMPT


class ImageGenAgent(
    BaseAgent,
    agent_type="image",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["dalle3", "download_image"],
):
    """图片生成Agent - 高优先级，所有平台"""

    agent_name = "image_agent"
    agent_description = (
        "负责根据输入具体的的描述生成图片；"
        "适用场景：图片生成"
    )
    agent_system_prompt = """
        生成图像的工具。
        输入应该是详细的英文图像描述，包含：
        - 主要对象和场景
        - 艺术风格（如：photorealistic, oil painting, digital art, anime style等）
        - 色彩和光线（如：warm colors, dramatic lighting, soft pastel等）
        - 构图和视角（如：close-up, aerial view, wide angle等）
        - 氛围和情绪（如：peaceful, energetic, mysterious等）
        
        描述越详细，生成效果越好。使用英文以获得最佳结果。
    """

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成图片生成 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = IMAGE_GEN_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
