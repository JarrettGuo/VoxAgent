#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : registry.py
"""

from typing import Dict, List

from langchain_core.tools import BaseTool

from src.core.tools.file import file_create
from src.core.tools.system import app_control
from src.utils.logger import logger


class ToolRegistry:
    """工具注册中心 - 管理所有可用工具"""

    def __init__(self):
        """初始化工具注册中心"""
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        # 系统工具
        self.register("app_control", app_control())

        # 文件工具
        self.register("file_create", file_create())

    def register(self, name: str, tool: BaseTool):
        """注册工具"""
        if name in self._tools:
            logger.warning(f"Tool {name} is already registered. Overwriting.")

        self._tools[name] = tool

    def get(self, name: str) -> BaseTool:
        """获取工具"""
        if name not in self._tools:
            raise ValueError(f"Tool {name} is not registered.")

        return self._tools[name]

    def get_all(self) -> List[BaseTool]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """根据类别获取工具"""
        # TODO: 实现更复杂的分类逻辑
        return [
            tool for name, tool in self._tools.items()
            if category in name
        ]


# 全局工具注册中心实例
tool_registry = ToolRegistry()
