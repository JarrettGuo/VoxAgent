#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : models.py
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Task(BaseModel):
    """任务定义"""
    task_id: str
    description: str  # 任务描述
    assigned_agent: str  # 分配的 Agent 名称
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class TaskResult(BaseModel):
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    iterations: int = 0
    tool_calls: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """执行计划"""
    plan_id: str
    tasks: List[Task]
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
