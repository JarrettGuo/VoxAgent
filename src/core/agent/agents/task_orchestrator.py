from typing import Dict, Any, Union

from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from src.core.agent.entities.agent_entity import ExecutionState, ExecutionStatus, StepState
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

        # 编译图
        compiled_graph = workflow.compile()

        logger.info(f"✅ {self.name} compiled successfully")
        return compiled_graph

    def _initialize_execution(self, state: ExecutionState) -> Dict[str, Any]:
        """初始化执行状态"""
        plan = state.plan if hasattr(state, 'plan') else state['plan']
        steps = plan.get("steps", [])

        # 将计划步骤转换为执行状态
        step_states = []
        for idx, step in enumerate(steps):
            step_states.append(StepState(
                step_id=step.get("task_id"),
                description=step.get("description", ""),
                agent_type=step.get("assigned_agent", "unknown"),
                parameters=step.get("parameters", {}),
                status=ExecutionStatus.PENDING,
                result=None,
                error=""
            ))

        # 返回需要更新的字段
        return {
            "steps": step_states,
            "current_step_index": 0,
            "completed": False,
            "execution_results": []
        }

    def _get_state_value(self, state: Union[ExecutionState, Dict], key: str, default=None):
        """统一获取 state 的值（支持 Pydantic Model 和 Dict）"""
        if isinstance(state, dict):
            return state.get(key, default)
        else:
            return getattr(state, key, default)

    def _check_completion(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """检查执行是否完成"""
        current_index = self._get_state_value(state, 'current_step_index', 0)
        steps = self._get_state_value(state, 'steps', [])
        total_steps = len(steps)

        logger.info(f"📊 Progress: {current_index}/{total_steps} steps")

        # 检查是否所有步骤都完成
        if current_index >= total_steps:
            return {"completed": True}

        return {}

    def _route_from_check(self, state: Union[ExecutionState, Dict]) -> str:
        """从检查节点决定下一步路由"""
        steps = self._get_state_value(state, 'steps', [])

        # 检查是否有错误
        for step in steps:
            step_status = step.status if hasattr(step, 'status') else step.get('status')
            if step_status == ExecutionStatus.FAILED:
                return "error"

        # 检查是否完成
        completed = self._get_state_value(state, 'completed', False)
        if completed:
            return "finish"

        # 继续执行下一步
        return "execute"

    def _execute_current_step(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """执行当前步骤"""
        current_index = self._get_state_value(state, 'current_step_index', 0)
        steps = self._get_state_value(state, 'steps', [])
        current_step = steps[current_index]

        # 获取步骤信息（支持 Pydantic 和 dict）
        description = current_step.description if hasattr(current_step, 'description') else current_step.get(
            'description')
        agent_type = current_step.agent_type if hasattr(current_step, 'agent_type') else current_step.get('agent_type')
        parameters = current_step.parameters if hasattr(current_step, 'parameters') else current_step.get('parameters',
                                                                                                          {})

        logger.info(f"▶️  Executing step {current_index + 1}: {description}")

        try:
            # 更新步骤状态为运行中
            if hasattr(current_step, 'status'):
                current_step.status = ExecutionStatus.RUNNING
            else:
                current_step['status'] = ExecutionStatus.RUNNING

            # 获取对应的agent
            agent = self.agents.get(agent_type)

            if not agent:
                raise ValueError(f"Unknown agent type: {agent_type}")

            # 构建 agent 输入
            agent_input = {
                "user_input": description,
                "parameters": parameters
            }

            # 执行agent
            result = agent.invoke(agent_input)

            # 检查执行结果
            if result.get("success"):
                if hasattr(current_step, 'status'):
                    current_step.status = ExecutionStatus.SUCCESS
                    current_step.result = result
                else:
                    current_step['status'] = ExecutionStatus.SUCCESS
                    current_step['result'] = result

                logger.info(f"✅ Step {current_index + 1} completed successfully")

                step_id = current_step.step_id if hasattr(current_step, 'step_id') else current_step.get('step_id')
                execution_result = {
                    "step_id": step_id,
                    "description": description,
                    "status": "success",
                    "result": result
                }
            else:
                # 任务执行失败但 agent 正常返回
                error_msg = result.get("output", "Unknown error")

                if hasattr(current_step, 'status'):
                    current_step.status = ExecutionStatus.FAILED
                    current_step.error = error_msg
                else:
                    current_step['status'] = ExecutionStatus.FAILED
                    current_step['error'] = error_msg

                logger.warning(f"⚠️  Step {current_index + 1} failed: {error_msg}")

                step_id = current_step.step_id if hasattr(current_step, 'step_id') else current_step.get('step_id')
                execution_result = {
                    "step_id": step_id,
                    "description": description,
                    "status": "failed",
                    "error": error_msg
                }

            execution_results = self._get_state_value(state, 'execution_results', [])
            return {
                "current_step_index": current_index + 1,
                "execution_results": execution_results + [execution_result],
                "steps": steps  # 返回更新后的 steps
            }

        except Exception as e:
            logger.error(f"❌ Step {current_index + 1} failed with exception: {str(e)}")

            if hasattr(current_step, 'status'):
                current_step.status = ExecutionStatus.FAILED
                current_step.error = str(e)
            else:
                current_step['status'] = ExecutionStatus.FAILED
                current_step['error'] = str(e)

            step_id = current_step.step_id if hasattr(current_step, 'step_id') else current_step.get('step_id')
            execution_result = {
                "step_id": step_id,
                "description": description,
                "status": "failed",
                "error": str(e)
            }

            execution_results = self._get_state_value(state, 'execution_results', [])
            return {
                "error_message": str(e),
                "execution_results": execution_results + [execution_result],
                "steps": steps
            }

    def _handle_error(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """处理执行错误"""
        error_message = self._get_state_value(state, 'error_message', 'Unknown error')
        logger.error(f"🔴 Execution failed: {error_message}")

        # 统计失败步骤
        steps = self._get_state_value(state, 'steps', [])
        failed_steps = []
        for s in steps:
            status = s.status if hasattr(s, 'status') else s.get('status')
            if status == ExecutionStatus.FAILED:
                failed_steps.append(s)

        error_msg = f"{error_message} 执行失败，{len(failed_steps)} 个步骤未完成"

        return {
            "completed": True,
            "error_message": error_msg
        }

    def _finalize_execution(self, state: Union[ExecutionState, Dict]) -> Dict[str, Any]:
        """完成执行"""
        steps = self._get_state_value(state, 'steps', [])

        successful_steps = 0
        for s in steps:
            status = s.status if hasattr(s, 'status') else s.get('status')
            if status == ExecutionStatus.SUCCESS:
                successful_steps += 1

        total_steps = len(steps)

        logger.info(f"🎉 Execution completed: {successful_steps}/{total_steps} steps successful")

        return {}

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行计划

        参数:
            plan: PlannerAgent返回的计划

        返回:
            执行结果
        """
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

        # 生成执行摘要
        return self._generate_summary(final_state)

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
            "message": self._create_message_from_dict(steps, successful_steps, total_steps)
        }

    def _create_message_from_dict(self, steps: list, successful: int, total: int) -> str:
        """创建用户友好的消息"""
        if successful == total:
            return f"成功执行了所有 {total} 个步骤！"
        elif successful == 0:
            return f"执行失败，所有步骤都未能完成。"
        else:
            return f"⚠部分完成：成功执行了 {successful}/{total} 个步骤。"
