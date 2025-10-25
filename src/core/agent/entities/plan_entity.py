#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : plan_entity.py
"""
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """单个计划步骤"""
    step_number: int = Field(description="步骤编号")
    assigned_agent: str = Field(description="执行该步骤的 Agent 类型")
    description: str = Field(description="步骤描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="步骤参数")
    expected_result: Optional[str] = Field(default=None, description="预期结果")


class PlannerOutput(BaseModel):
    """Planner 输出格式"""
    task: str = Field(description="原始任务描述")
    feasibility: str = Field(description="可行性：feasible, infeasible, invalid_input")
    reason: str = Field(description="可行性分析说明")
    steps: List[PlanStep] = Field(default_factory=list, description="任务步骤")
