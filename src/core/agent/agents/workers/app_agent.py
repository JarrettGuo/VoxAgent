from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import APP_CONTROL_AGENT_PROMPT


class AppAgent(
    BaseAgent,
    agent_type="app_control",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["app_control"],
):
    """App Agent"""

    agent_name = "app_agent"
    agent_description = (
        "负责开启和关闭应用程序"
        "适用场景：打开浏览器，记事本"
    )
    agent_system_prompt = """你是能够操作应用的开关。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = APP_CONTROL_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
