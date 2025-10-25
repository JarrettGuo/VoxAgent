from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import SEARCH_AGENT_PROMPT


class SearchAgent(
    BaseAgent,
    agent_type="search",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["wikipedia_search", "duckduckgo_search"],
):
    """浏览器操作 Agent"""

    agent_name = "browser_agent"
    agent_description = "打开网页、搜索信息"
    agent_system_prompt = SEARCH_AGENT_PROMPT
