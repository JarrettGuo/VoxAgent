from typing import Dict, Any

from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from src.core.agent.entities.agent_entity import ExecutionState, ExecutionStatus
from src.utils.logger import logger


class TaskOrchestrator:

    name: str = "task_orchestrator"
    agents: Dict[str, Any] = {}

    def __init__(self, agents: Dict[str, Any]):
        """
        初始化执行协调器

        参数:
            agents: 可用的agent字典，key为agent类型，value为agent实例
        """
        self.agents = agents
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> CompiledStateGraph:
        """构建 LangGraph 图结构"""
        workflow = StateGraph(ExecutionState)

        # 添加节点
        workflow.add_node("initialize", self._initialize_execution)
        workflow.add_node("check_completion", self._check_completion)
        workflow.add_node("execute_step", self._execute_current_step)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("finalize", self._finalize_execution)

        # 设置入口点
        workflow.set_entry_point("initialize")

        # 添加边
        workflow.add_edge("initialize", "check_completion")

        # 条件路由：检查是否完成
        workflow.add_conditional_edges(
            "check_completion",
            self._route_from_check,
            {
                "execute": "execute_step",
                "finish": "finalize",
                "error": "handle_error"
            }
        )

        # 执行步骤后继续检查
        workflow.add_edge("execute_step", "check_completion")

        # 错误处理后结束
        workflow.add_edge("handle_error", END)
        workflow.add_edge("finalize", END)

        # 5. 编译图
        compiled_graph = workflow.compile()

        logger.info(f"✅ {self.name} compiled successfully")
        return compiled_graph

    def _initialize_execution(self, state: ExecutionState) -> ExecutionState:
        """初始化执行状态"""
        logger.info("🚀 Initializing execution...")

        plan = state["plan"]
        steps = plan.get("steps", [])

        # 将计划步骤转换为执行状态
        step_states = []
        for idx, step in enumerate(steps):
            step_states.append({
                "step_id": f"step_{idx}",
                "description": step.get("description", ""),
                "agent_type": step.get("agent", "unknown"),
                "status": ExecutionStatus.PENDING,
                "result": None,
                "error": ""
            })

        return {
            "steps": step_states,
            "current_step_index": 0,
            "completed": False,
            "execution_results": []
        }

    def _check_completion(self, state: ExecutionState) -> ExecutionState:
        """检查执行是否完成"""
        current_index = state["current_step_index"]
        total_steps = len(state["steps"])

        logger.info(f"📊 Progress: {current_index}/{total_steps} steps")

        # 检查是否有失败的步骤
        for step in state["steps"]:
            if step["status"] == ExecutionStatus.FAILED:
                return state

        # 检查是否所有步骤都完成
        if current_index >= total_steps:
            return {**state, "completed": True}

        return state

    def _route_from_check(self, state: ExecutionState) -> str:
        """从检查节点决定下一步路由"""
        # 检查是否有错误
        for step in state["steps"]:
            if step["status"] == ExecutionStatus.FAILED:
                return "error"

        # 检查是否完成
        if state["completed"]:
            return "finish"

        # 继续执行下一步
        return "execute"

    def _execute_current_step(self, state: ExecutionState) -> ExecutionState:
        """执行当前步骤"""
        current_index = state["current_step_index"]
        current_step = state["steps"][current_index]

        logger.info(f"▶️  Executing step {current_index + 1}: {current_step['description']}")

        try:
            # 更新步骤状态为运行中
            current_step["status"] = ExecutionStatus.RUNNING

            # 获取对应的agent
            agent_type = current_step["agent_type"]
            agent = self.agents.get(agent_type)

            if not agent:
                raise ValueError(f"Unknown agent type: {agent_type}")

            # 执行agent
            result = agent.execute(current_step["description"])

            # 更新步骤状态
            current_step["status"] = ExecutionStatus.SUCCESS
            current_step["result"] = result

            logger.info(f"✅ Step {current_index + 1} completed successfully")

            # 记录执行结果
            execution_result = {
                "step_id": current_step["step_id"],
                "description": current_step["description"],
                "status": "success",
                "result": result
            }

            return {
                "current_step_index": current_index + 1,
                "execution_results": [execution_result]
            }

        except Exception as e:
            logger.error(f"❌ Step {current_index + 1} failed: {str(e)}")

            # 更新步骤状态为失败
            current_step["status"] = ExecutionStatus.FAILED
            current_step["error"] = str(e)

            execution_result = {
                "step_id": current_step["step_id"],
                "description": current_step["description"],
                "status": "failed",
                "error": str(e)
            }

            return {
                "error_message": str(e),
                "execution_results": [execution_result]
            }

    def _handle_error(self, state: ExecutionState) -> ExecutionState:
        """处理执行错误"""
        logger.error(f"🔴 Execution failed: {state.get('error_message', 'Unknown error')}")

        # 可以在这里添加重试逻辑或回滚逻辑
        failed_steps = [s for s in state["steps"] if s["status"] == ExecutionStatus.FAILED]

        return {
            "completed": True,
            "error_message": f"{state.get('error_message')} 执行失败，{len(failed_steps)} 个步骤未完成"
        }

    def _finalize_execution(self, state: ExecutionState) -> ExecutionState:
        """完成执行"""
        successful_steps = sum(1 for s in state["steps"] if s["status"] == ExecutionStatus.SUCCESS)
        total_steps = len(state["steps"])

        logger.info(f"🎉 Execution completed: {successful_steps}/{total_steps} steps successful")

        return state

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行计划

        参数:
            plan: PlannerAgent返回的计划

        返回:
            执行结果
        """
        initial_state = {
            "plan": plan,
            "current_step_index": 0,
            "steps": [],
            "execution_results": [],
            "completed": False,
            "error_message": ""
        }

        # 运行工作流
        final_state = self.workflow.invoke(initial_state)

        # 生成执行摘要
        return self._generate_summary(final_state)

    def _generate_summary(self, state: ExecutionState) -> Dict[str, Any]:
        """生成执行摘要"""
        total_steps = len(state["steps"])
        successful_steps = sum(1 for s in state["steps"] if s["status"] == ExecutionStatus.SUCCESS)
        failed_steps = sum(1 for s in state["steps"] if s["status"] == ExecutionStatus.FAILED)

        return {
            "success": failed_steps == 0,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "results": state["execution_results"],
            "error_message": state.get("error_message", ""),
            "message": self._create_message(state)
        }

    def _create_message(self, state: ExecutionState) -> str:
        """创建用户友好的消息"""
        total = len(state["steps"])
        successful = sum(1 for s in state["steps"] if s["status"] == ExecutionStatus.SUCCESS)

        if successful == total:
            return f"✅ 成功执行了所有 {total} 个步骤！"
        elif successful == 0:
            return f"❌ 执行失败，所有步骤都未能完成。"
        else:
            return f"⚠️  部分完成：成功执行了 {successful}/{total} 个步骤。"