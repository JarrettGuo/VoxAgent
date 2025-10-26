#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : planner_agent.py
"""

import json
import uuid
from typing import Dict, Any, Optional, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from src.core.agent.entities.agent_prompts import PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE
from src.core.agent.entities.plan_entity import PlannerOutput, PlanStep
from src.core.models import ExecutionPlan, Task, TaskStatus
from src.utils.logger import logger


class PlannerAgent:
    """LLM 任务规划器 - 将用户输入转换为标准化的执行计划"""

    def __init__(self, llm: BaseChatModel, available_agents: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.available_agents = available_agents or {}

        # 构建 Agent 信息
        self.agent_info = self._format_agent_info()

        logger.info(
            f"Planner initialized with {len(self.available_agents)} agents"
        )

    def _format_agent_info(self) -> str:
        """格式化 Agent 信息供 LLM 参考"""
        if not self.available_agents:
            return "Planner has no available agents."

        lines = []
        for agent_type, agent in self.available_agents.items():
            ability = agent.get_ability_info()
            lines.append(
                f"- {agent_type}: {ability['description']}\n"
                f"  工具: {', '.join(ability['tools'])}"
            )

        return "\n".join(lines)

    async def plan(self, user_query: str, conversation_history: Optional[List[BaseMessage]] = None) -> ExecutionPlan:
        """生成执行计划（异步）"""
        try:
            # 1. 构建提示词
            system_prompt = PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                agent_info=self.agent_info
            )

            # 2. 调用 LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]

            if conversation_history:
                messages.extend(conversation_history)
                logger.info(
                    f"Planning with {len(conversation_history)} "
                    f"history messages"
                )
            else:
                # 如果没有历史，使用单轮查询
                messages.append(HumanMessage(content=user_query))

            response = await self.llm.ainvoke(messages)
            response_content = response.content.strip()

            # 3. 解析响应
            planner_output = self._parse_response(response_content, user_query)

            # 4. 转换为 ExecutionPlan
            execution_plan = self._convert_to_execution_plan(planner_output)

            logger.info(
                f"Generated plan with {len(execution_plan.tasks)} tasks "
                f"(feasibility: {planner_output.feasibility})"
            )

            return execution_plan

        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)

            # 返回空计划
            return self._create_empty_plan(user_query, error=str(e))

    def plan_sync(self, user_query: str, conversation_history: Optional[List[BaseMessage]] = None) -> ExecutionPlan:
        """生成执行计划（同步）"""
        import asyncio
        return asyncio.run(self.plan(user_query, conversation_history))

    def _parse_response(self, response: str, original_task: str) -> PlannerOutput:
        """解析 LLM 响应为 PlannerOutput"""
        try:
            json_str = response.strip()

            # 移除 Markdown 代码块
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()

            # 解析 JSON
            plan_dict = json.loads(json_str)

            # 验证必要字段
            if "feasibility" not in plan_dict:
                raise ValueError("Missing 'feasibility' field")

            # 验证 feasibility 值
            valid_feasibility = ["feasible", "infeasible", "invalid_input"]
            if plan_dict["feasibility"] not in valid_feasibility:
                raise ValueError(f"Invalid feasibility value: {plan_dict['feasibility']}")

            # 转换 steps
            steps = []
            for step_dict in plan_dict.get("steps", []):
                steps.append(PlanStep(**step_dict))

            return PlannerOutput(
                task=plan_dict.get("task", original_task),
                feasibility=plan_dict["feasibility"],
                reason=plan_dict.get("reason", ""),  # ← 新增
                steps=steps
            )

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            logger.warning(f"Response: {response[:200]}...")
            return PlannerOutput(
                task=original_task,
                feasibility="invalid_input",
                reason=f"LLM 返回的不是有效的 JSON 格式",
                steps=[]
            )

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return PlannerOutput(
                task=original_task,
                feasibility="invalid_input",
                reason=f"解析错误: {str(e)}",
                steps=[]
            )

    def _convert_to_execution_plan(self, planner_output: PlannerOutput) -> ExecutionPlan:
        """将 PlannerOutput 转换为 ExecutionPlan"""
        plan_id = str(uuid.uuid4())

        # 构建 metadata
        metadata = {
            "feasibility": planner_output.feasibility,
            "reason": planner_output.reason,  # ← 新增
            "original_task": planner_output.task
        }

        # 检查可行性
        if planner_output.feasibility != "feasible":
            return ExecutionPlan(
                plan_id=plan_id,
                tasks=[],
                dependencies={},
                metadata=metadata
            )

        # 转换步骤为 Task 列表
        tasks = []
        for step in planner_output.steps:
            task_id = str(uuid.uuid4())

            task = Task(
                task_id=task_id,
                description=step.description,
                assigned_agent=step.assigned_agent,
                metadata={
                    "step_number": step.step_number,
                    "expected_result": step.expected_result
                },
                status=TaskStatus.PENDING
            )

            tasks.append(task)

        metadata["total_steps"] = len(tasks)

        return ExecutionPlan(
            plan_id=plan_id,
            tasks=tasks,
            dependencies={},
            metadata=metadata
        )

    def _create_empty_plan(self, user_query: str, error: Optional[str] = None) -> ExecutionPlan:
        """创建空计划（用于错误情况）"""
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            tasks=[],
            dependencies={},
            metadata={
                "original_query": user_query,
                "error": error,
                "feasibility": "error"
            }
        )

    def update_available_agents(self, agents: Dict[str, Any]):
        """更新可用 Agent 列表"""
        self.available_agents = agents
        self.agent_info = self._format_agent_info()
        logger.info(f"Updated {len(agents)} available agents")
