#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : registry.py
"""
import platform
from typing import Dict, List

from langchain_core.tools import BaseTool

from src.core.tools.file import file_create, file_read, file_search, file_list, file_find_recent, file_delete, \
    file_append, file_write
from src.core.tools.image import dalle3
from src.core.tools.search import duckduckgo_search, wikipedia_search
from src.core.tools.system import app_control
from src.core.tools.weather import gaode_weather
from src.utils.config import config
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
        self.register("file_read", file_read())
        self.register("file_write", file_write())
        self.register("file_append", file_append())
        self.register("file_delete", file_delete())
        self.register("file_search", file_search())
        self.register("file_list", file_list())
        self.register("file_find_recent", file_find_recent())

        # 搜索工具
        try:
            self.register("duckduckgo_search", duckduckgo_search())
        except Exception as e:
            logger.warning(f"DuckDuckGo registration failed: {e}")

        try:
            self.register("wikipedia_search", wikipedia_search())
        except Exception as e:
            logger.warning(f"Wikipedia registration failed: {e}")

        # 天气工具
        try:
            api_key = config.get("gaode_weather.api_key")
            self.register("gaode_weather", gaode_weather(api_key=api_key))
        except Exception as e:
            logger.warning(f"Gaode Weather registration failed: {e}")

        # 图像工具
        try:
            api_key = config.get("openai.api_key")
            self.register("dalle3", dalle3(api_key=api_key))
        except Exception as e:
            logger.warning(f"DALL·E 3 registration failed: {e}")

        # macOS 专用工具
        if platform.system() == "Darwin":  # 仅在 macOS 上注册
            self._register_macos_tools()

    def register(self, name: str, tool: BaseTool):
        """注册工具"""
        if name in self._tools:
            logger.warning(f"Tool {name} is already registered. Overwriting.")

        self._tools[name] = tool

    def _register_macos_tools(self):
        """注册 macOS 专用工具"""
        try:
            from src.core.tools.system.macos import (
                mail_search, mail_read, mail_send,
                music_play, music_control, music_search
            )

            # 邮件工具
            self.register("mail_search", mail_search())
            self.register("mail_read", mail_read())
            self.register("mail_send", mail_send())

            # 音乐工具
            self.register("music_play", music_play())
            self.register("music_control", music_control())
            self.register("music_search", music_search())

            logger.info("macOS 专用工具注册成功")

        except Exception as e:
            logger.warning(f"macOS 工具注册失败: {e}")

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
        category_map = {
            "system": ["app_control"],
            "file": ["file_create", "file_read", "file_write", "file_append",
                     "file_delete", "file_search", "file_list", "file_find_recent"],
            "search": ["duckduckgo_search", "wikipedia_search"],
            "weather": ["gaode_weather"],
            "image": ["dalle3"],
            "macos_mail": ["mail_search", "mail_read", "mail_send"],
            "macos_music": ["music_play", "music_control", "music_search"],
        }

        tool_names = category_map.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]


# 全局工具注册中心实例
tool_registry = ToolRegistry()
