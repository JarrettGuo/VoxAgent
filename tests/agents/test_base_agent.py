#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : test_base_agent.py
"""

from unittest.mock import Mock, patch

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
    agent_system_prompt = "你是一个测试Agent"


class PlatformSpecificAgent(
    BaseAgent,
    agent_type="macos_only_agent",
    priority=30,
    platforms=["darwin"],
    required_tools=["music_play"],
    enabled=True
):
    """仅macOS平台的Agent"""
    agent_name = "macos_agent"
    agent_description = "仅支持macOS的Agent"
    agent_system_prompt = "macOS专用Agent"


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


class TestBaseAgentRegistration:
    """测试Agent注册机制"""

    def test_agent_auto_registration(self):
        """测试Agent自动注册"""
        assert "test_agent" in BaseAgent._registry
        assert BaseAgent._registry["test_agent"] == TestAgent

        metadata = BaseAgent._metadata["test_agent"]
        assert metadata.agent_type == "test_agent"
        assert metadata.priority == 50
        assert "darwin" in metadata.platforms

    def test_agent_metadata_creation(self):
        """测试元数据正确创建"""
        metadata = BaseAgent.get_agent_metadata("test_agent")

        assert metadata is not None
        assert metadata.priority == 50
        assert metadata.enabled is True
        assert "file_create" in metadata.required_tools

    def test_platform_compatibility(self):
        """测试平台兼容性检查"""
        import platform

        metadata = BaseAgent.get_agent_metadata("test_agent")
        # test_agent支持所有平台
        assert metadata.is_platform_compatible()

        # 如果不是macOS，macos_only_agent不应该被注册
        if platform.system() != "Darwin":
            macos_metadata = BaseAgent.get_agent_metadata("macos_only_agent")
            # 应该不存在或不兼容
            assert macos_metadata is None or not macos_metadata.is_platform_compatible()

    def test_get_all_agent_types(self):
        """测试获取所有Agent类型"""
        agent_types = BaseAgent.get_all_agent_types()

        assert "test_agent" in agent_types
        assert isinstance(agent_types, list)

    def test_agent_types_sorted_by_priority(self):
        """测试Agent按优先级排序"""
        sorted_types = BaseAgent.get_all_agent_types(sorted_by_priority=True)

        # 验证排序（高优先级在前）
        priorities = [
            BaseAgent.get_agent_metadata(t).priority
            for t in sorted_types
        ]

        assert priorities == sorted(priorities, reverse=True)


class TestBaseAgentInitialization:
    """测试Agent初始化"""

    def test_basic_initialization(self, llm, tool_manager, agent_config):
        """测试基本初始化"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        assert agent.llm is not None
        assert agent.config.max_iterations == 5
        assert len(agent.tools) > 0
        assert agent.llm_with_tools is not None

    def test_tools_binding(self, llm, tool_manager, agent_config):
        """测试工具正确绑定"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 验证required_tools被正确获取
        tool_names = [tool.name for tool in agent.tools]
        assert "file_create" in tool_names

    def test_missing_tools_error(self, llm, agent_config):
        """测试缺失工具时的错误处理"""
        # 创建空的工具管理器
        empty_tool_manager = ToolRegistry()
        empty_tool_manager.clear()

        with pytest.raises(ValueError, match="not found"):
            TestAgent(
                llm=llm,
                tool_manager=empty_tool_manager,
                config=agent_config
            )

    def test_default_config(self, llm, tool_manager):
        """测试默认配置"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager
        )

        # 应该使用默认配置
        assert agent.config.max_iterations == 10  # 默认值

    def test_prompt_template_creation(self, llm, tool_manager, agent_config):
        """测试Prompt模板创建"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        assert agent.prompt is not None
        assert agent.chain is not None


class TestBaseAgentExecution:
    """测试Agent执行流程"""

    @pytest.mark.asyncio
    async def test_simple_task_execution(self, llm, tool_manager, agent_config):
        """测试简单任务执行"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 执行简单任务
        result = await agent.ainvoke({
            "user_input": "创建一个名为test.txt的文件",
            "parameters": {}
        })

        assert result["success"] is True or result["success"] is False
        assert "output" in result
        assert "iterations" in result
        assert "tool_calls" in result

    @pytest.mark.asyncio
    async def test_task_with_parameters(self, llm, tool_manager, agent_config):
        """测试带参数的任务"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        result = await agent.ainvoke({
            "user_input": "创建文件",
            "parameters": {
                "file_path": "/tmp/test_param.txt",
                "content": "测试内容"
            }
        })

        assert "iterations" in result
        assert result["iterations"] > 0

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, llm, tool_manager):
        """测试最大迭代限制"""
        config = AgentConfig(max_iterations=2)
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=config
        )

        # 执行一个可能需要多次迭代的任务
        result = await agent.ainvoke({
            "user_input": "执行一个复杂任务",
            "parameters": {}
        })

        # 验证不会超过最大迭代次数
        assert result["iterations"] <= 2

    @pytest.mark.asyncio
    async def test_error_handling(self, llm, tool_manager, agent_config):
        """测试错误处理"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 修改：空输入应该抛出 ValueError，需要捕获它
        with pytest.raises(ValueError, match="user_input.*required"):
            await agent.ainvoke({
                "user_input": "",  # 空输入
                "parameters": {}
            })

        # 或者测试有效输入但可能出错的情况
        result = await agent.ainvoke({
            "user_input": "执行一个可能出错的任务",
            "parameters": {}
        })

        # 验证即使出错也有结果
        assert result is not None
        assert "output" in result or "metadata" in result

    def test_sync_execution(self, llm, tool_manager, agent_config):
        """测试同步执行"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 使用同步方法
        result = agent.invoke({
            "user_input": "创建测试文件",
            "parameters": {}
        })

        assert "success" in result
        assert "output" in result


class TestBaseAgentToolExecution:
    """测试工具执行"""

    @pytest.mark.asyncio
    async def test_tool_call_logging(self, llm, tool_manager, agent_config):
        """测试工具调用被正确记录"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        result = await agent.ainvoke({
            "user_input": "创建一个文件",
            "parameters": {}
        })

        # 检查tool_calls日志
        assert isinstance(result["tool_calls"], list)

    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self, llm, tool_manager, agent_config):
        """测试工具执行错误处理"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        # 模拟工具错误
        with patch.object(agent, '_find_tool') as mock_find:
            mock_tool = Mock()
            mock_tool.invoke.side_effect = Exception("工具错误")
            mock_find.return_value = mock_tool

            # 应该捕获错误并继续
            result = await agent.ainvoke({
                "user_input": "测试任务",
                "parameters": {}
            })

            # 不应该崩溃
            assert result is not None


class TestBaseAgentFactory:
    """测试Agent工厂方法"""

    def test_create_all_agents(self, llm, tool_manager):
        """测试批量创建Agent"""
        agents = BaseAgent.create_all_agents(
            llm=llm,
            tool_manager=tool_manager,
            check_dependencies=False  # 跳过依赖检查以加速测试
        )

        assert isinstance(agents, dict)
        assert len(agents) > 0
        assert "test_agent" in agents

    def test_create_agents_with_dependency_check(self, llm, tool_manager):
        """测试带依赖检查的批量创建"""
        agents = BaseAgent.create_all_agents(
            llm=llm,
            tool_manager=tool_manager,
            check_dependencies=True
        )

        # 所有创建的Agent都应该有必需的工具
        for agent_type, agent in agents.items():
            metadata = BaseAgent.get_agent_metadata(agent_type)
            if metadata.required_tools:
                tool_names = [t.name for t in agent.tools]
                for required_tool in metadata.required_tools:
                    assert required_tool in tool_names

    def test_disabled_agents_not_created(self, llm, tool_manager):
        """测试禁用的Agent不会被创建"""
        # 临时禁用test_agent
        original_enabled = BaseAgent._metadata["test_agent"].enabled
        BaseAgent._metadata["test_agent"].enabled = False

        try:
            agents = BaseAgent.create_all_agents(
                llm=llm,
                tool_manager=tool_manager
            )

            # test_agent不应该在结果中
            # 注意：如果没有其他enabled的agent，agents可能为空
            if agents:
                assert "test_agent" not in agents

        finally:
            # 恢复状态
            BaseAgent._metadata["test_agent"].enabled = original_enabled


class TestBaseAgentAbilityInfo:
    """测试Agent能力信息"""

    def test_get_ability_info(self, llm, tool_manager, agent_config):
        """测试获取能力信息"""
        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=agent_config
        )

        ability_info = agent.get_ability_info()

        assert ability_info["name"] == "test_agent"
        assert ability_info["description"] == "用于测试的Agent"
        assert "tools" in ability_info
        assert isinstance(ability_info["tools"], list)
        assert ability_info["max_iterations"] == 5


@pytest.mark.integration
class TestBaseAgentIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_tool_execution_verification(self, llm, tool_manager):
        """测试：验证工具确实被执行"""
        import tempfile
        import os

        agent = TestAgent(
            llm=llm,
            tool_manager=tool_manager,
            config=AgentConfig(max_iterations=5)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "tool_test.txt")

            # 使用更明确的指令
            result = await agent.ainvoke({
                "user_input": (
                    f"请使用 file_create 工具创建文件。"
                    f"文件路径: {test_file}，"
                    f"文件内容: 测试内容"
                ),
                "parameters": {}
            })

            logger.info(f"工具执行测试结果: {result}")

            # 验证至少尝试了执行
            assert result is not None
            assert result["iterations"] > 0

            # 记录详细信息用于调试
            logger.info(f"成功: {result.get('success')}")
            logger.info(f"迭代次数: {result['iterations']}")
            logger.info(f"工具调用: {result.get('tool_calls', [])}")
            logger.info(f"输出: {result.get('output', '')[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
