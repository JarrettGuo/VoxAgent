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
    agent_description = "处理文件读写、搜索等操作"
    agent_system_prompt = FILE_MANAGEMENT_AGENT_PROMPT
