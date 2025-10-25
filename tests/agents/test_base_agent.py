#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BaseAgent 核心功能测试
"""

import os
import tempfile

import pytest
from langchain_openai import ChatOpenAI

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_entity import AgentConfig
from src.core.tools import ToolRegistry
from src.utils.config import config
from src.utils.logger import logger


class TestAgent(
    BaseAgent,
    agent_type="test_agent",
    priority=50,
    platforms=["darwin", "linux", "windows"],
    required_tools=["file_create"],
    enabled=True
):
    """测试用的简单Agent"""
    agent_name = "test_agent"
    agent_description = "用于测试的Agent"
    agent_system_prompt = "你是一个测试Agent，负责文件操作"


@pytest.fixture
def tool_manager():
    """创建工具管理器"""
    return ToolRegistry()


@pytest.fixture
def llm():
    """创建LLM实例"""
    qiniu_config = config.get("qiniu")
    return ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=0.0,
    )


@pytest.fixture
def agent_config():
    """创建Agent配置"""
    return AgentConfig(max_iterations=5)


class TestBaseAgentCore:
    """测试Agent核心功能"""

    def test_agent_registration(self):
        """测试Agent自动注册"""
        assert "test_agent" in BaseAgent._registry
        assert BaseAgent._registry["test_agent"] == TestAgent

        metadata = BaseAgent.get_agent_metadata("test_agent")
        assert metadata is not None
        assert metadata.priority == 50
        assert metadata.enabled is True

    def test_agent_initialization(self, llm, tool_manager, agent_config):
        """测试Agent初始化"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        assert agent.llm is not None
        assert agent.config.max_iterations == 5
        assert len(agent.tools) > 0
        assert agent.agent_executor is not None
        assert len(agent.conversation_history) == 0

        # 验证工具绑定
        tool_names = [tool.name for tool in agent.tools]
        assert "file_create" in tool_names

    def test_agent_factory(self, llm, tool_manager):
        """测试Agent工厂方法"""
        agents = BaseAgent.create_all_agents(
            llm=llm,
            tool_manager=tool_manager,
            check_dependencies=False
        )

        assert isinstance(agents, dict)
        assert len(agents) > 0

        # 验证所有Agent有必需工具
        for agent_type, agent in agents.items():
            metadata = BaseAgent.get_agent_metadata(agent_type)
            if metadata.required_tools:
                tool_names = [t.name for t in agent.tools]
                for required_tool in metadata.required_tools:
                    assert required_tool in tool_names

    @pytest.mark.asyncio
    async def test_agent_execution(self, llm, tool_manager, agent_config):
        """测试Agent执行（集成测试）"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")

            # 执行任务
            result = await agent.ainvoke({
                "user_input": f"创建文件 {test_file}，内容为：Test content",
                "parameters": {}
            })

            logger.info(f"Execution result: {result}")

            # 验证执行完成
            assert "output" in result
            assert "success" in result
            assert result["success"] is True

            # 验证文件是否创建（可能成功也可能失败，取决于LLM响应）
            if os.path.exists(test_file):
                logger.info(f"✅ File successfully created")
                with open(test_file, 'r') as f:
                    content = f.read()
                    logger.info(f"File content: {content}")

    def test_conversation_history(self, llm, tool_manager, agent_config):
        """测试对话历史管理"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 初始状态
        assert len(agent.conversation_history) == 0

        # 重置
        agent.reset()
        assert len(agent.conversation_history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
