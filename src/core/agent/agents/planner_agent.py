#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : planner_agent.py
"""

import json
import uuid
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.constants import END
from langgraph.graph.state import StateGraph, CompiledStateGraph

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_entity import AgentState
from src.core.agent.entities.agent_prompts import PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE
from src.core.agent.entities.queue_entity import QueueEvent, AgentThought
from src.utils.logger import logger


class TaskPlan(dict):
    """任务计划数据结构"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def is_invalid_input(self) -> bool:
        """判断是否为无效输入"""
        return self.get("feasibility") == "invalid_input"

    @property
    def is_infeasible(self) -> bool:
        """判断任务是否不可行"""
        return self.get("feasibility") == "infeasible"

    @property
    def steps(self) -> list:
        """获取任务步骤"""
        return self.get("steps", [])


class PlannerAgent(BaseAgent):
    """
    任务规划 Agent - 负责将用户意图转换为可执行的任务计划

    功能：
    1. 输入验证：检查用户输入是否有效
    2. 可行性评估：判断任务是否在计算机能力范围内
    3. 任务分解：将复杂任务分解为可执行的步骤
    4. 输出结构化计划：JSON 格式的任务计划

    图结构：
    START -> validate_and_plan -> END / Other Agent Calls (if needed)
    """

    name: str = "planner_agent"

    def _build_agent(self) -> CompiledStateGraph:
        """构建 LangGraph 图结构"""
        # 1. 创建状态图
        graph = StateGraph(AgentState)

        # 2. 添加节点
        graph.add_node("validate_and_plan", self._validate_and_plan_node)

        # 3. 设置入口点
        graph.set_entry_point("validate_and_plan")

        # 4. 直接结束
        graph.add_edge("validate_and_plan", END)

        # 5. 编译图
        compiled_graph = graph.compile()

        logger.info(f"✅ {self.name} graph compiled successfully")
        return compiled_graph

    def _validate_and_plan_node(self, state: AgentState) -> AgentState:
        """
        验证输入并生成任务计划节点

        流程：
        1. 提取用户输入
        2. 构建带有系统提示词的消息
        3. 调用 LLM 生成计划
        4. 解析并验证计划
        5. 发布事件
        """
        task_id = state["task_id"]
        user_input = state["messages"][-1].content

        logger.info(f"🧠 Planning task: {user_input}")

        # 1. 发布开始思考事件
        self._queue_manager.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.AGENT_THOUGHT,
            thought=f"正在分析任务: {user_input}",
        ))

        try:
            # 2. 构建消息（添加系统提示词）
            messages = [
                SystemMessage(content=PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE),
                state["messages"][-1]
            ]

            # 3. 调用 LLM 生成计划
            response = self.llm.invoke(messages)
            response_content = response.content.strip()

            logger.debug(f"📋 LLM response: {response_content[:200]}...")

            # 4. 解析计划
            task_plan = self._parse_plan(response_content, user_input)

            # 5. 根据计划类型发布不同事件
            if task_plan.is_invalid_input:
                # 无效输入
                message = "输入内容无法理解，请重新表述您的需求。"
                self._publish_final_message(task_id, message, task_plan)

            elif task_plan.is_infeasible:
                # 任务不可行
                message = "抱歉，这个任务超出了我的能力范围。我只能执行计算机相关的操作。"
                self._publish_final_message(task_id, message, task_plan)

            else:
                # 有效计划
                steps_summary = self._format_steps_summary(task_plan.steps)
                message = f"我已经为您制定了计划：\n\n{steps_summary}"
                self._publish_final_message(task_id, message, task_plan)

            # 6. 发布结束事件
            self._queue_manager.publish(task_id, AgentThought(
                id=uuid.uuid4(),
                task_id=task_id,
                event=QueueEvent.AGENT_END,
            ))

            # 7. 返回更新后的状态
            return {
                "messages": [AIMessage(content=message)],
                "is_finished": True,
                "final_output": message,
                "metadata": {"plan": task_plan}
            }

        except Exception as e:
            logger.error(f"❌ Planning failed: {e}")
            error_message = f"规划任务时出错: {str(e)}"

            self._queue_manager.publish(task_id, AgentThought(
                id=uuid.uuid4(),
                task_id=task_id,
                event=QueueEvent.ERROR,
                observation=error_message,
            ))

            return {
                "messages": [AIMessage(content=error_message)],
                "is_finished": True,
                "final_output": error_message,
            }

    def _parse_plan(self, response: str, original_task: str) -> TaskPlan:
        """解析 LLM 响应为结构化计划，将 JSON 转换为 TaskPlan 对象"""
        # 检查特殊标记
        if "---Invalid Input---" in response:
            return TaskPlan({
                "task": original_task,
                "feasibility": "invalid_input",
                "steps": []
            })

        if "---Infeasible Task---" in response:
            return TaskPlan({
                "task": original_task,
                "feasibility": "infeasible",
                "steps": []
            })

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分（可能被包裹在 markdown 代码块中）
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()

            # 解析 JSON
            plan_dict = json.loads(json_str)

            # 验证必要字段
            if "steps" not in plan_dict:
                raise ValueError("Plan missing 'steps' field")

            # 确保有 feasibility 字段
            if "feasibility" not in plan_dict:
                plan_dict["feasibility"] = "feasible"

            return TaskPlan(plan_dict)

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Failed to parse JSON plan: {e}")
            logger.warning(f"Response: {response[:200]}...")

            # 返回默认的不可行计划
            return TaskPlan({
                "task": original_task,
                "feasibility": "infeasible",
                "steps": [],
                "error": f"Failed to parse plan: {str(e)}"
            })

        except Exception as e:
            logger.error(f"❌ Error parsing plan: {e}")
            return TaskPlan({
                "task": original_task,
                "feasibility": "infeasible",
                "steps": [],
                "error": str(e)
            })

    def _format_steps_summary(self, steps: list) -> str:
        """格式化步骤摘要"""
        if not steps:
            return "无具体步骤"

        summary_lines = []
        for step in steps[:5]:  # 最多显示前 5 步
            step_num = step.get("step_number", "?")
            action = step.get("action", "未知操作")
            summary_lines.append(f"{step_num}. {action}")

        if len(steps) > 5:
            summary_lines.append(f"... 还有 {len(steps) - 5} 个步骤")

        return "\n".join(summary_lines)

    def _publish_final_message(
            self,
            task_id,
            message: str,
            plan: Optional[TaskPlan] = None
    ):
        """发布最终消息事件"""
        metadata = {}
        if plan:
            metadata = dict(plan)

        self._queue_manager.publish(task_id, AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.AGENT_MESSAGE,
            observation=message,
            metadata=metadata
        ))

    def plan_task(self, task_description: str) -> Dict[str, Any]:
        """便捷方法：直接规划任务（同步调用"""
        result = self.invoke({"user_input": task_description})

        return {
            "success": result.is_finished,
            "message": result.output,
            "plan": result.metadata.get("plan", {})
        }
