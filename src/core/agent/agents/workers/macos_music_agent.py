from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import create_platform_prompt, MUSIC_AGENT_PROMPT


class MacMusicAgent(
    BaseAgent,
    agent_type="macos_music",
    priority=80,  # High priority - frequently used
    platforms=["darwin"],
    required_tools=["music_play", "music_control", "music_search"],
):
    """MacOS Music Agent"""

    agent_name = "mac_music_agent"
    agent_description = (
        "负责控制 Apple Music 的搜索与播放操作"
        "适用场景：播放音乐，切换歌曲，搜索音乐"
    )
    agent_system_prompt = """你能够操作 Apple Music。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = create_platform_prompt(MUSIC_AGENT_PROMPT, 'music', 'mac')

        return prompt_template.format(tools_section=tools_section)
