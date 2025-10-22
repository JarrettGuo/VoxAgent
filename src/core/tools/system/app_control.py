#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : app_control.py
"""

import platform
import subprocess
from typing import Any, Type, Dict, ClassVar

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import AppControlSchema
from src.utils.logger import logger


class AppControlTool(BaseTool):
    """应用程序控制工具 - 打开或关闭应用程序"""

    name: str = "app_control"
    description: str = "用于打开或关闭计算机上的应用程序。支持的操作：打开应用、关闭应用"
    args_schema: Type[AppControlSchema] = AppControlSchema

    # macOS 应用名称映射
    APP_MAP: ClassVar[Dict[str, str]] = {  # 所有的类共享这个变量
        "chrome": "Google Chrome",
        "浏览器": "Google Chrome",
        "微信": "WeChat",
        "wechat": "WeChat",
        "记事本": "TextEdit",
        "vscode": "Visual Studio Code",
        "终端": "Terminal",
        "terminal": "Terminal",
    }

    def _run(self, app_name: str, action: str, **kwargs: Any) -> str:
        """执行应用程序控制"""
        try:
            # 标准化应用名称
            normalized_app = self.APP_MAP.get(app_name.lower(), app_name)

            if action == "open":
                return self._open_app(normalized_app)
            elif action == "close":
                return self._close_app(normalized_app)
            else:
                return f"Not supported action: {action}"

        except Exception as e:
            error_msg = f"failed to {action} app {app_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _open_app(self, app_name: str) -> str:
        """打开应用程序"""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-a", app_name], check=True)
                return f"Opened app: {app_name}"

            elif system == "Windows":
                subprocess.run(["start", app_name], shell=True, check=True)
                return f"Opened app: {app_name}"

            elif system == "Linux":
                subprocess.run([app_name], check=True)
                return f"Opened app: {app_name}"

            else:
                return f"Not supported operating system: {system}"

        except Exception as e:
            return f"Error opening app {app_name}: {str(e)}"

    def _close_app(self, app_name: str) -> str:
        """关闭应用程序"""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                # 使用 AppleScript 关闭应用
                script = f'tell application "{app_name}" to quit'
                subprocess.run(["osascript", "-e", script], check=True)
                return f"Closed app: {app_name}"

            elif system == "Windows":
                subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"], check=True)
                return f"Closed app: {app_name}"

            elif system == "Linux":
                subprocess.run(["pkill", "-f", app_name], check=True)
                return f"Closed app: {app_name}"

            else:
                return f"Not supported operating system: {system}"

        except Exception as e:
            return f"Error closing app {app_name}: {str(e)}"


def app_control(**kwargs) -> BaseTool:
    """工厂函数：创建应用程序控制工具实例"""
    return AppControlTool(**kwargs)
