#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TaskOrchestrator 集成测试
"""

import pytest
from langchain_openai import ChatOpenAI

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.agents.task_orchestrator import TaskOrchestrator
from src.core.tools import tool_registry
from src.utils.config import config
from src.utils.langsmith_setup import setup_langsmith
from src.utils.logger import logger


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """初始化测试环境"""
    setup_langsmith()
    logger.info("\n" + "=" * 70)
    logger.info(" " * 15 + "TASK ORCHESTRATOR TEST SUITE")
    logger.info("=" * 70 + "\n")


@pytest.fixture(scope="module")
def llm():
    """创建 LLM 实例"""
    qiniu_config = config.get("qiniu")
    return ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
        temperature=0.7,
    )


@pytest.fixture(scope="module")
def agents(llm):
    """创建所有可用的 agents"""
    # ✅ 关键修复：显式导入具体的 agent 类（不是通过 __init__.py）
    from src.core.agent.agents.workers.file_agent import FileManagementAgent
    from src.core.agent.agents.workers.search_agent import SearchAgent

    # 验证注册
    all_types = BaseAgent.get_all_agent_types()
    logger.info(f"Registered agent types: {all_types}")

    # 如果注册表为空，说明导入有问题
    if not all_types:
        logger.error("❌ No agents in registry after import!")
        logger.error("This should not happen. Check agent class definitions.")
        raise RuntimeError("Agent registration failed")

    # ✅ 根据调试脚本，关闭依赖检查也能成功创建
    agents = BaseAgent.create_all_agents(
        llm=llm,
        tool_manager=tool_registry,
        check_dependencies=False  # 先关闭依赖检查
    )

    logger.info(f"✓ Created {len(agents)} agents: {list(agents.keys())}")

    # 如果还是失败，打印详细信息
    if len(agents) == 0:
        logger.error("❌ Failed to create agents via create_all_agents()")
        logger.error("Attempting manual creation for debugging...")

        agents = {}

        # 手动创建每个 agent
        try:
            agents["file"] = FileManagementAgent(
                llm=llm,
                tool_manager=tool_registry
            )
            logger.info("✓ Manually created FileManagementAgent")
        except Exception as e:
            logger.error(f"✗ Manual FileManagementAgent creation failed: {e}")
            import traceback
            traceback.print_exc()

        try:
            agents["search"] = SearchAgent(
                llm=llm,
                tool_manager=tool_registry
            )
            logger.info("✓ Manually created SearchAgent")
        except Exception as e:
            logger.error(f"✗ Manual SearchAgent creation failed: {e}")
            import traceback
            traceback.print_exc()

    assert len(agents) > 0, f"No agents were created. Registry: {BaseAgent._registry}"

    return agents


@pytest.fixture
def orchestrator(agents):
    """创建 TaskOrchestrator 实例"""
    return TaskOrchestrator(agents)


class TestTaskOrchestrator:
    """TaskOrchestrator 功能测试"""

    def test_simple_single_step(self, orchestrator):
        """测试简单的单步执行"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST: Simple Single-Step Execution")
        logger.info("=" * 70)

        plan = {
            "steps": [{
                "task_id": "task-test-001",
                "description": "搜索 Python 编程语言的信息",
                "assigned_agent": "search",
                "parameters": {}
            }]
        }

        result = orchestrator.execute(plan)

        logger.info(f"\n📊 Results:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Total Steps: {result['total_steps']}")
        logger.info(f"  Successful Steps: {result['successful_steps']}")
        logger.info(f"  Message: {result['message']}")

        assert result['success'] is True
        assert result['total_steps'] == 1
        assert result['successful_steps'] == 1

        logger.info("✅ Test passed!")

    def test_multi_step_execution(self, orchestrator):
        """测试多步骤顺序执行"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST: Multi-Step Execution")
        logger.info("=" * 70)

        plan = {
            "steps": [
                {
                    "task_id": "task-002",
                    "description": "搜索人工智能的定义",
                    "assigned_agent": "search",
                    "parameters": {}
                },
                {
                    "task_id": "task-003",
                    "description": "创建文件 /tmp/ai_notes.txt",
                    "assigned_agent": "file",
                    "parameters": {
                        "file_path": "/tmp/ai_notes.txt",
                        "content": "AI learning notes"
                    }
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"\n📊 Results:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Total Steps: {result['total_steps']}")
        logger.info(f"  Successful Steps: {result['successful_steps']}")

        assert result['success'] is True
        assert result['total_steps'] == 2
        assert result['successful_steps'] == 2

        logger.info("✅ Test passed!")

    def test_unknown_agent_handling(self, orchestrator):
        """测试未知 agent 类型的错误处理"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST: Unknown Agent Error Handling")
        logger.info("=" * 70)

        plan = {
            "steps": [{
                "task_id": "task-004",
                "description": "使用不存在的 agent",
                "assigned_agent": "nonexistent_agent",
                "parameters": {}
            }]
        }

        result = orchestrator.execute(plan)

        logger.info(f"\n📊 Results:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Failed Steps: {result['failed_steps']}")
        logger.info(f"  Error: {result['error_message']}")

        assert result['success'] is False
        assert result['failed_steps'] == 1
        assert "Unknown agent type" in result['error_message']

        logger.info("✅ Test passed!")

    def test_partial_execution_failure(self, orchestrator):
        """测试部分步骤失败的情况"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST: Partial Execution Failure")
        logger.info("=" * 70)

        plan = {
            "steps": [
                {
                    "task_id": "task-005",
                    "description": "搜索 Python 信息",
                    "assigned_agent": "search",
                    "parameters": {}
                },
                {
                    "task_id": "task-006",
                    "description": "调用不存在的 agent",
                    "assigned_agent": "invalid_agent",
                    "parameters": {}
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"\n📊 Results:")
        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Total Steps: {result['total_steps']}")
        logger.info(f"  Successful: {result['successful_steps']}")
        logger.info(f"  Failed: {result['failed_steps']}")

        assert result['success'] is False
        assert result['total_steps'] == 2
        assert result['successful_steps'] == 1
        assert result['failed_steps'] == 1

        logger.info("✅ Test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
