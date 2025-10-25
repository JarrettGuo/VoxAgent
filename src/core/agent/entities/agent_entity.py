#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : agent_entity.py
"""
import platform
from enum import Enum
from typing import List, Dict, Any
from typing import Optional

from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Agent 元数据"""
    agent_type: str
    priority: int = Field(default=50, ge=0, le=100)
    platforms: Optional[List[str]] = None
    required_tools: Optional[List[str]] = None
    enabled: bool = True

    def is_platform_compatible(self) -> bool:
        if not self.platforms:
            return True

        current_platform = platform.system().lower()
        return current_platform in [p.lower() for p in self.platforms]

    def check_tools_available(self, tool_manager) -> bool:
        if not self.required_tools:
            return True

        available_tools = set(tool_manager.get_all_tool_names())
        required_tools = set(self.required_tools)

        return required_tools.issubset(available_tools)


class AgentConfig(BaseModel):
    """Agent 配置"""
    max_iterations: int = Field(default=10, ge=1, le=50)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    model: str = "gpt-4o-mini"
    timeout: int = 300


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class StepState(BaseModel):
    """单个步骤的状态"""
    step_id: str
    description: str
    agent_type: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Any] = None
    error: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # 执行追踪
    iteration_count: int = 0


class ExecutionState(BaseModel):
    """执行状态 - 用于 LangGraph"""
    plan: Dict[str, Any] = Field(default_factory=dict)
    steps: List[StepState] = Field(default_factory=list)
    current_step_index: int = 0
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)
    completed: bool = False
    error_message: str = ""

    class Config:
        arbitrary_types_allowed = True
