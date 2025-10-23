from langchain_classic.agents import initialize_agent, AgentType
from langchain_core.language_models import BaseChatModel

from src.core.agent.agents.workers.base_worker_agent import BaseWorkerAgent
from src.core.tools import ToolRegistry


class SearchAgent(
    BaseWorkerAgent,
    agent_type="search",
    priority=80,  # High priority - frequently used
    required_tools=["wikipedia_search"],
):
    """文件管理Agent - 高优先级，所有平台"""

    def __init__(self, tool_manager: ToolRegistry, llm: BaseChatModel, name=None, description=None, **kwargs):
        super().__init__(
            name=name or "SearchAgent",
            description= description or "处理所有联网查询操作",
            tools=[
                "duckduckgo_search", "wikipedia_search"
            ],
            llm=llm,
            tool_manager=tool_manager
        )

        self.agent = initialize_agent(
            tools=self.tool_manager.get_tools_by_category("search"),
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
        )

    def run(self, task: str) -> str:
        """Execute a user or planner-issued task."""
        return self.agent.run(task)