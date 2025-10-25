import asyncio
from typing import Dict, Any, Union

from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from src.core.agent.entities.agent_entity import (
    ExecutionState, ExecutionStatus, StepState
)
from src.utils.logger import logger


class TaskOrchestrator:
    """
    任务协调器 - 使用 LangGraph 管理执行流程
    """

    name: str = "task_orchestrator"
    agents: Dict[str, Any] = {}

    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.workflow = self._build_workflow()
        logger.info(f"TaskOrchestrator initialized with {len(agents)} agents")

    def _build_workflow(self) -> CompiledStateGraph:
        """构建简化的 LangGraph 工作流"""
        workflow = StateGraph(ExecutionState)

        # 只需要 3 个节点
        workflow.add_node("initialize", self._initialize_execution)
        workflow.add_node("execute_step", self._execute_step)  # ← 合并原来的 agent_step + execute_tool
        workflow.add_node("finalize", self._finalize_execution)

        workflow.set_entry_point("initialize")

        workflow.add_edge("initialize", "execute_step")

        # execute_step 之后直接判断是否继续
        workflow.add_conditional_edges(
            "execute_step",
            self._route_after_execution,
            {
                "next_step": "execute_step",
                "all_done": "finalize",
                "error": "finalize"
            }
        )

        workflow.add_edge("finalize", END)

        compiled = workflow.compile()
        logger.info("LangGraph workflow compiled")
        return compiled

    def _initialize_execution(self, state: ExecutionState) -> Dict[str, Any]:
        """初始化执行状态"""
        plan = state.plan if hasattr(state, 'plan') else state['plan']
        steps = plan.get("steps", [])

        logger.info(f"Initializing execution with {len(steps)} steps")

        # 转换步骤
        step_states = []
        for idx, step in enumerate(steps):
            step_states.append(StepState(
                step_id=step.get("task_id"),
                description=step.get("description", ""),
                agent_type=step.get("assigned_agent", "unknown"),
                parameters=step.get("parameters", {}),
                status=ExecutionStatus.PENDING,
                iteration_count=0
            ))

        return {
            "steps": step_states,
            "current_step_index": 0,
            "execution_results": [],
            "completed": False
        }

    def _execute_step(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """执行单个步骤（AgentExecutor 自动处理所有工具调用）"""
        current_index = self._get_state_value(state, 'current_step_index', 0)
        steps = self._get_state_value(state, 'steps', [])

        if current_index >= len(steps):
            return {"error_message": "Step index out of range"}

        current_step = steps[current_index]

        logger.info(
            f"Step {current_index + 1}/{len(steps)}: "
            f"{current_step.agent_type} - {current_step.description}"
        )

        # 获取 agent
        agent = self.agents.get(current_step.agent_type)
        if not agent:
            error_msg = f"Unknown agent type: {current_step.agent_type}"
            logger.error(f"{error_msg}")
            current_step.status = ExecutionStatus.FAILED
            current_step.error = error_msg
            return {
                "steps": steps,
                "current_step_index": current_index + 1,
                "error_message": error_msg
            }

        # 重置 agent 的对话历史
        agent.reset()

        try:
            # 调用 agent
            result = asyncio.run(agent.ainvoke({
                "user_input": current_step.description,
                "parameters": current_step.parameters
            }))

            # 检查执行结果
            if not result.get("success"):
                current_step.status = ExecutionStatus.FAILED
                current_step.error = result.get("error", "Unknown error")
                logger.error(f"Step failed: {current_step.error}")
                return {
                    "steps": steps,
                    "current_step_index": current_index + 1,
                    "error_message": current_step.error
                }

            # 标记成功
            current_step.status = ExecutionStatus.SUCCESS
            current_step.result = result["output"]
            current_step.iteration_count = result["iterations"]

            # 提取工具调用详情
            tool_calls = []
            for step_tuple in result.get("intermediate_steps", []):
                agent_action, observation = step_tuple
                tool_calls.append({
                    "tool": agent_action.tool,
                    "args": agent_action.tool_input,
                    "result": observation
                })

            # 记录执行结果
            execution_results = self._get_state_value(state, 'execution_results', [])
            execution_results.append({
                "step_id": current_step.step_id,
                "description": current_step.description,
                "status": "success",
                "output": result["output"],
                "iterations": result["iterations"],
                "tool_calls": tool_calls
            })

            return {
                "steps": steps,
                "execution_results": execution_results,
                "current_step_index": current_index + 1
            }

        except Exception as e:
            logger.error(f"Step execution error: {e}", exc_info=True)
            current_step.status = ExecutionStatus.FAILED
            current_step.error = str(e)
            return {
                "steps": steps,
                "current_step_index": current_index + 1,
                "error_message": str(e)
            }

    def _route_after_execution(self, state: Union[ExecutionState, Dict]) -> str:
        """决定下一步的路由逻辑"""
        error_message = self._get_state_value(state, 'error_message', '')
        if error_message:
            return "error"

        current_index = self._get_state_value(state, 'current_step_index', 0)
        steps = self._get_state_value(state, 'steps', [])

        if current_index >= len(steps):
            return "all_done"
        else:
            return "next_step"

    def _finalize_execution(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """完成执行"""
        steps = self._get_state_value(state, 'steps', [])

        successful_steps = sum(
            1 for s in steps
            if (s.status if hasattr(s, 'status') else s.get('status')) == ExecutionStatus.SUCCESS
        )

        logger.info(f"🎉 Execution finalized: {successful_steps}/{len(steps)} successful")

        return {"completed": True}

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行计划（外部接口）
        """
        logger.info("=" * 70)
        logger.info("Starting TaskOrchestrator execution")
        logger.info("=" * 70)

        # 创建初始状态
        initial_state = ExecutionState(
            plan=plan,
            current_step_index=0,
            steps=[],
            execution_results=[],
            completed=False,
            error_message=""
        )

        # 运行工作流
        final_state = self.workflow.invoke(initial_state)

        # 生成摘要
        summary = self._generate_summary(final_state)

        logger.info("=" * 70)
        logger.info(f"Execution complete: {summary['message']}")
        logger.info("=" * 70)

        return summary

    def _generate_summary(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """生成执行摘要"""
        steps = self._get_state_value(state, 'steps', [])
        total_steps = len(steps)

        successful_steps = 0
        failed_steps = 0

        for s in steps:
            status = s.status if hasattr(s, 'status') else s.get('status')
            if status == ExecutionStatus.SUCCESS:
                successful_steps += 1
            elif status == ExecutionStatus.FAILED:
                failed_steps += 1

        execution_results = self._get_state_value(state, 'execution_results', [])
        error_message = self._get_state_value(state, 'error_message', '')

        return {
            "success": failed_steps == 0,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "results": execution_results,
            "error_message": error_message,
            "message": self._create_message(steps, successful_steps, total_steps)
        }

    def _create_message(self, steps: list, successful: int, total: int) -> str:
        """创建用户友好的消息"""
        if successful == total:
            return f"成功执行了所有 {total} 个步骤！"
        elif successful == 0:
            return f"执行失败，所有步骤都未能完成。"
        else:
            return f"部分完成：成功执行了 {successful}/{total} 个步骤。"

    @staticmethod
    def _get_state_value(state: Union[ExecutionState, Dict], key: str, default=None):
        """统一获取 state 的值"""
        if isinstance(state, dict):
            return state.get(key, default)
        else:
            return getattr(state, key, default)
