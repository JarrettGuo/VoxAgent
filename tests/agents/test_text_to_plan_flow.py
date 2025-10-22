#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : test_text_to_plan_flow.py
"""

import sys
from pathlib import Path

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
    logger.info("=" * 60)
    logger.info("🧪 测试文本到计划的完整流程")
    logger.info("=" * 60)

    try:
        # 1. 创建 PlannerAgent
        logger.info("\n📦 步骤 1: 初始化 PlannerAgent")

        from src.core.agent.agents.planner_agent import PlannerAgent
        from src.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI

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

        agent_config = AgentConfig(max_iterations=5)

        agent = PlannerAgent(
            name="test_planner",
            llm=llm,
            config=agent_config,
        )

        logger.info("✅ PlannerAgent 初始化成功")

        # 2. 模拟用户输入
        logger.info("\n📝 步骤 2: 模拟用户语音输入")

        user_commands = [
            "帮我打开浏览器,搜索今天北京的天气",
            "帮我创建一个名为 meeting_notes.txt 的文件",
            "帮我订一张去上海的高铁票",
        ]

        # 3. 对每个命令进行规划
        for i, command in enumerate(user_commands, 1):
            logger.info(f"\n{'=' * 40}")
            logger.info(f"📝 测试 {i}: {command}")
            logger.info("=" * 40)

            # ✅ 修改: 使用 plan_task() 方法而不是 invoke()
            result = agent.plan_task(command)

            logger.info(f"✅ 成功: {result.get('success', False)}")
            logger.info(f"✅ 消息: {result.get('message', '')}")

            plan = result.get("plan", {})
            if plan:
                logger.info(f"✅ 可行性: {plan.get('feasibility', 'unknown')}")
                steps = plan.get("steps", [])
                if steps:
                    logger.info(f"✅ 步骤数: {len(steps)}")
                    for idx, step in enumerate(steps, 1):
                        logger.info(f"  {idx}. {step.get('action', step.get('description', ''))}")

        logger.info("\n✅ 测试完成!")

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_text_to_plan_flow()
