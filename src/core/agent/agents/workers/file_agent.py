from langchain_classic.agents import initialize_agent, AgentType
from langchain_core.language_models import BaseChatModel

from src.core.agent.agents.workers.base_worker_agent import BaseWorkerAgent
from src.core.tools import ToolRegistry


class FileManagementAgent(
    BaseWorkerAgent,
    agent_type="file",
    priority=80,  # High priority - frequently used
    required_tools=["file_create", "file_read", "file_write"],
):
    """文件管理Agent - 高优先级，所有平台"""

    def __init__(self, tool_manager: ToolRegistry, llm: BaseChatModel, name=None, description=None, **kwargs):
        super().__init__(
            name=name or "FileManagement",
            description= description or "处理所有文件系统操作",
            tools=[
                "file_append", "file_create", "file_delete", "file_find_recent",
                "file_list", "file_read", "file_search", "file_write"
            ],
            llm=llm,
            tool_manager=tool_manager
        )

        self.agent = initialize_agent(
            tools=self.tool_manager.get_tools_by_category("file"),
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
        )

    def run(self, task: str) -> str:
        """Execute a user or planner-issued task."""
        return self.agent.run(task)