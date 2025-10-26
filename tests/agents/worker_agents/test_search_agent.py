#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from langchain_openai import ChatOpenAI

from src.core.tools import tool_registry
from src.utils.config import config


class MockLLM:
    """A mock LLM that simulates structured tool calls."""

    def predict(self, *args, **kwargs):
        return (
            "Action: wikipedia_search\n"
            "Action Input: {'query': 'Python programming language'}"
        )

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)


class MockTool:
    """Simulate a LangChain Tool."""

    def __init__(self, name, output):
        self.name = name
        self.output = output

    def _run(self, *args, **kwargs):
        return self.output


@pytest.fixture
def mock_agent():
    from src.core.agent.agents.workers.search_agent import SearchAgent
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
        max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
    )
    return SearchAgent(tool_manager=tool_registry, llm=llm)


def test_search_agent_run(mock_agent):
    query = "Search for Python programming language"
    result = mock_agent.run(query)

    print(f"result is {result}")

    assert "Python" in result
    print("✅ SearchAgent returned:", result)
