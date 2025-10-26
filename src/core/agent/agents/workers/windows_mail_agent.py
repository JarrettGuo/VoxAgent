from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import WINDOWS_MAIL_AGENT_PROMPT


class WinMailAgent(
    BaseAgent,
    agent_type="windows_mail",
    priority=80,  # High priority - frequently used
    platforms=["windows"],
    required_tools=["outlook_search", "outlook_read"],
):
    """Windows Mail Agent"""

    agent_name = "windows_mail_agent"
    agent_description = (
        "负责控制 Microsoft Outlook 的操作"
        "适用场景：查询邮件，阅读邮件"
    )
    agent_system_prompt = """你能够操作 Microsoft Outlook 应用。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = WINDOWS_MAIL_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
