#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : test_planner_agent.py
"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : test_text_to_plan_flow.py
"""

import sys
from pathlib import Path

from src.utils.langsmith_setup import setup_langsmith

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger
from src.utils.config import config


def test_text_to_plan_flow():
    """
    测试: 文本 → PlannerAgent → 计划
    (跳过录音和 ASR,直接测试规划部分)
    """
    setup_langsmith()
    logger.info("=" * 60)
    logger.info("🧪 测试文本到计划的完整流程")
    logger.info("=" * 60)

    try:
        # 1. 创建可用的 Agents
        logger.info("\n📦 步骤 1: 初始化 Worker Agents")

        from langchain_openai import ChatOpenAI
        from src.core.agent.agents.base_agent import BaseAgent
        from src.core.agent.agents.planner_agent import PlannerAgent
        from src.core.tools import tool_registry

        # ✅ 显式导入 worker agents 以触发注册
        from src.core.agent.agents.workers.file_agent import FileManagementAgent
        from src.core.agent.agents.workers.search_agent import SearchAgent

        # ✅ 从配置文件中读取七牛云配置
        qiniu_config = config.get("qiniu")
        if not qiniu_config:
            raise ValueError("❌ 未找到七牛云配置,请检查 config/config.yaml")

        # ✅ 使用七牛云配置创建 LLM
        llm = ChatOpenAI(
            api_key=qiniu_config.get("api_key"),
            base_url=qiniu_config.get("base_url"),
            model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
            temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
            max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
        )

        # ✅ 创建所有可用的 agents
        agents = BaseAgent.create_all_agents(
            llm=llm,
            tool_manager=tool_registry,
            check_dependencies=False
        )

        logger.info(f"✅ 创建了 {len(agents)} 个 worker agents: {list(agents.keys())}")

        # 2. 创建 PlannerAgent
        logger.info("\n📦 步骤 2: 初始化 PlannerAgent")

        planner = PlannerAgent(
            llm=llm,
            available_agents=agents  # ✅ 传入可用的 agents
        )

        logger.info("✅ PlannerAgent 初始化成功")

        # 3. 模拟用户输入
        logger.info("\n📝 步骤 3: 模拟用户语音输入")

        user_commands = [
            "帮我搜索今天北京的天气",
            "帮我创建一个名为 meeting_notes.txt 的文件",
            "帮我订一张去上海的高铁票",
        ]

        # 4. 对每个命令进行规划
        for i, command in enumerate(user_commands, 1):
            logger.info(f"\n{'=' * 40}")
            logger.info(f"📝 测试 {i}: {command}")
            logger.info("=" * 40)

            # ✅ 使用正确的方法: plan_sync()
            execution_plan = planner.plan_sync(command)

            # ✅ 打印 ExecutionPlan 的信息
            logger.info(f"计划 ID: {execution_plan.plan_id}")
            logger.info(f"可行性: {execution_plan.metadata.get('feasibility', 'unknown')}")
            logger.info(f"原因: {execution_plan.metadata.get('reason', '')}")
            logger.info(f"任务数: {len(execution_plan.tasks)}")

            if execution_plan.tasks:
                logger.info(f"\n📋 执行步骤:")
                for idx, task in enumerate(execution_plan.tasks, 1):
                    logger.info(f"  {idx}. [{task.assigned_agent}] {task.description}")
                    if task.parameters:
                        logger.info(f"     参数: {task.parameters}")
            else:
                logger.info(f"  (无执行步骤)")

        logger.info("\n✅ 测试完成!")

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_text_to_plan_flow()
