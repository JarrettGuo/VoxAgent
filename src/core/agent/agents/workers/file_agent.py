from typing import List

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import FILE_MANAGEMENT_AGENT_PROMPT


class FileManagementAgent(
    BaseAgent,
    agent_type="file",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["file_create", "file_read", "file_write"],
):
    """文件管理Agent - 高优先级，所有平台"""

    agent_name = "file_agent"
    agent_description = (
        "负责所有文件系统操作，包括：创建、读取、写入、追加、删除文件；"
        "搜索文件、列出目录内容、查找最近修改的文件。"
        "适用场景：创建文档、编辑配置文件、整理文件、查找文件等"
    )
    agent_system_prompt = """你是一个专业的文件管理助手，负责帮助用户完成文件操作任务。"""

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成文件管理 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = FILE_MANAGEMENT_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)
