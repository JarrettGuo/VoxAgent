from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import MAC_MAIL_AGENT_PROMPT


class MacMailAgent(
    BaseAgent,
    agent_type="macos_music",
    priority=80,  # High priority - frequently used
    platforms=["darwin"],
    required_tools=["mail_search", "mail_read"],
):
    """MacOS Mail Agent"""

    agent_name = "mac_mail_agent"
    agent_description = (
        "负责控制 Apple Mail 的操作"
        "适用场景：查询邮件，阅读邮件"
    )
    agent_system_prompt = """你能够操作 Apple Mail 应用。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成搜索 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = MAC_MAIL_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
