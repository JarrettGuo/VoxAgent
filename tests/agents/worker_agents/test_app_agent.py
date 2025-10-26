import pytest
from langchain_openai import ChatOpenAI

from src.core.agent.agents.workers.app_agent import AppAgent
from src.core.tools import tool_registry
from src.utils.config import config
from src.utils.langsmith_setup import setup_langsmith


@pytest.fixture
def mock_agent():
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
        max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
    )
    return AppAgent(tool_manager=tool_registry, llm=llm)

def test_app_agent_run(mock_agent):
    setup_langsmith()
    query = "帮我打开记事本"
    result = mock_agent.invoke({
        "user_input": query,
    })

    print("✅ AppAgent returned:", result)

    query = "帮我关掉记事本"
    result = mock_agent.invoke({
        "user_input": query,
    })

    print("✅ AppAgent returned:", result)

    query = "帮我打开英雄联盟"
    result = mock_agent.invoke({
        "user_input": query,
    })

    print("✅ AppAgent returned:", result)