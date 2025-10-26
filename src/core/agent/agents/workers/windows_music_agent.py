from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import create_platform_prompt, MUSIC_AGENT_PROMPT


class WinMusicAgent(
    BaseAgent,
    agent_type="windows_music",
    priority=80,  # High priority - frequently used
    platforms=["windows"],
    required_tools=["pygame_music_play", "pygame_music_control", "pygame_music_search"],
):
    """Windows Music Agent"""

    agent_name = "windows_music_agent"
    agent_description = (
        "负责控制音乐的搜索与播放操作"
        "适用场景：播放音乐，切换歌曲"
    )
    agent_system_prompt = """你能够操作一个音乐播放器。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = create_platform_prompt(MUSIC_AGENT_PROMPT, 'music', 'windows')

        return prompt_template.format(tools_section=tools_section)
