#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : agent_entity.py
"""
import operator
import platform
from enum import Enum
from typing import List, Optional, Dict, Any, TypedDict, Annotated
from uuid import UUID

from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

from src.core.tools import ToolRegistry
from src.utils.logger import logger


class AgentConfig(BaseModel):
    """Agent 配置类 - 管理 Agent 的核心配置，包括迭代控制、系统提示词、工具绑定等"""

    # 基础配置
    max_iterations: int = 10  # 最大迭代次数
    enable_memory: bool = True  # 是否启用记忆

    # 提示词配置
    system_prompt: Optional[str] = None  # 系统提示词

    # 工具配置
    tools: List[BaseTool] = Field(default_factory=list)  # 绑定的工具列表

    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True  # 允许任意类型(如 BaseTool)


class AgentState(MessagesState):
    """Agent 状态类 - 继承 LangGraph 的 MessagesState"""

    task_id: UUID  # 任务唯一ID
    iteration_count: int  # 当前迭代次数
    is_finished: bool  # 是否完成
    final_output: Optional[str]  # 最终输出
    history: List[AnyMessage]  # 短期记忆历史
    metadata: Dict[str, Any]  # 额外元数据

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"

class StepState(TypedDict):
    step_id: str
    description: str
    agent_type: str
    status: ExecutionStatus
    result: Any
    error: str

class ExecutionState(TypedDict):
    plan: Dict[str, Any]
    current_step_index: int
    steps: List[StepState]
    execution_results: Annotated[List[Dict], operator.add]
    completed: bool
    error_message: str


class AgentMetadata:
    """Agent元数据"""

    def __init__(
            self,
            agent_type: str,
            priority: int = 50,
            platforms: Optional[List[str]] = None,
            required_tools: Optional[List[str]] = None,
            enabled: bool = True
    ):
        self.agent_type = agent_type
        self.priority = priority
        self.platforms = platforms or []  # 空列表表示所有平台
        self.required_tools = required_tools or []
        self.enabled = enabled

    def is_platform_compatible(self) -> bool:
        if not self.platforms:
            return True

        current_platform = platform.system()
        platform_map = {
            "Darwin": "macos",
            "Linux": "linux",
            "Windows": "windows"
        }

        current = platform_map.get(current_platform, "unknown")
        return current in self.platforms

    def check_tools_available(self, tool_manager: ToolRegistry) -> bool:
        if not self.required_tools:
            return True

        for tool_name in self.required_tools:
            if not tool_manager.has_tool(tool_name):
                logger.warning(
                    f"Agent '{self.agent_type}' requires tool '{tool_name}' which is not available"
                )
                return False
        return True
