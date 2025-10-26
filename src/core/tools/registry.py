#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : registry.py
"""

import platform
from typing import Dict, List, Optional

from langchain_core.tools import BaseTool

from src.core.tools import dalle3
# 导入工具
from src.core.tools.file import (
    file_create, file_read, file_search, file_list,
    file_find_recent, file_delete, file_append, file_write
)
from src.core.tools.image import image_download
from src.core.tools.search import duckduckgo_search, wikipedia_search, google_serper
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
        """注册默认工具（保持原有逻辑）"""
        # 系统工具
        self.register(app_control())

        # 文件工具
        self.register(file_create())
        self.register(file_read())
        self.register(file_write())
        self.register(file_append())
        self.register(file_delete())
        self.register(file_search())
        self.register(file_list())
        self.register(file_find_recent())

        # 搜索工具
        try:
            self.register(duckduckgo_search())
        except Exception as e:
            logger.warning(f"DuckDuckGo registration failed: {e}")

        try:
            self.register(wikipedia_search())
        except Exception as e:
            logger.warning(f"Wikipedia registration failed: {e}")

        try:
            api_key = config.get("google_serper.api_key")
            if api_key:
                self.register(google_serper(api_key=api_key))
            else:
                logger.warning("Google Serper API key not configured, skipping")
        except Exception as e:
            logger.warning(f"Google Serper registration failed: {e}")

        # 天气工具
        try:
            api_key = config.get("gaode_weather.api_key")
            if api_key:
                self.register(gaode_weather(api_key=api_key))
        except Exception as e:
            logger.warning(f"Gaode Weather registration failed: {e}")

        # 图像工具
        try:
            api_key = config.get("openai.api_key")
            self.register(dalle3(api_key=api_key))
        except Exception as e:
            logger.warning(f"DALL·E 3 registration failed: {e}")
        self.register(image_download())

        # macOS 专用工具
        if platform.system() == "Darwin":
            self._register_macos_tools()

        if platform.system() == "Windows":
            self._register_windows_tools()

    def register(self, tool: BaseTool, name: Optional[str] = None) -> None:
        """注册工具"""
        # 自动从 tool 对象获取名称
        tool_name = name or tool.name

        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")

        self._tools[tool_name] = tool
        logger.debug(f"Registered tool: {tool_name}")

    def get_tool(self, tool_name: str) -> BaseTool:
        """获取单个工具"""
        if tool_name not in self._tools:
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {list(self._tools.keys())}"
            )
        return self._tools[tool_name]

    def get_tools_by_names(self, tool_names: List[str]) -> List[BaseTool]:
        """批量获取工具"""
        return [self.get_tool(name) for name in tool_names]

    def get_all_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具实例"""
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"🗑️  Unregistered tool: {tool_name}")
            return True
        return False

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        logger.info("🗑️  Cleared all tools")

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """根据类别获取工具"""
        category_map = {
            "system": ["app_control"],
            "file": [
                "file_create", "file_read", "file_write", "file_append",
                "file_delete", "file_search", "file_list", "file_find_recent"
            ],
            "search": ["duckduckgo_search", "wikipedia_search"],
            "weather": ["gaode_weather"],
            "image": ["dalle3", "download_image"],
            "macos_mail": ["mail_search", "mail_read"],
            "macos_music": ["music_play", "music_control", "music_search"],
            "windows_mail": ["outlook_search", "outlook_read"],
            "windows_music": ["pygame_music_play", "pygame_music_control", "pygame_music_search",
                              "pygame_music_fetch"],
        }

        tool_names = category_map.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_tool_info(self) -> List[Dict[str, str]]:
        """获取所有工具的信息"""
        tool_info = []
        for tool in self._tools.values():
            tool_info.append({
                "name": tool.name,
                "description": tool.description,
            })
        return tool_info

    def _register_macos_tools(self):
        """注册 macOS 专用工具"""
        try:
            from src.core.tools.system.macos import (
                mail_search, mail_read, mail_send,
                music_play, music_control, music_search
            )

            # 邮件工具
            self.register(mail_search())
            self.register(mail_read())
            # self.register(mail_send())

            # 音乐工具
            self.register(music_play())
            self.register(music_control())
            self.register(music_search())

            logger.info("macOS tools registered")

        except Exception as e:
            logger.warning(f"macOS tools registration failed: {e}")

    def _register_windows_tools(self):
        """注册 macOS 专用工具"""
        try:
            from src.core.tools.system.windows import (
                outlook_send, outlook_read, outlook_search,
                pygame_music_search, pygame_music_play, pygame_music_control, pygame_music_fetch
            )

            # 邮件工具
            self.register(outlook_search())
            self.register(outlook_read())
            # self.register(outlook_send())

            # 音乐工具
            self.register(pygame_music_search())
            self.register(pygame_music_play())
            self.register(pygame_music_control())
            self.register(pygame_music_fetch())

            logger.info("windows tools registered")

        except Exception as e:
            logger.warning(f"windows tools registration failed: {e}")


# 全局工具注册中心实例
tool_registry = ToolRegistry()
