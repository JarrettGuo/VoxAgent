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

    # 多平台映射
    APP_MAP: ClassVar[Dict[str, Dict[str, Any]]] = {
        "chrome": {
            "Darwin": "Google Chrome",
            "Windows": {
                "exe": "chrome.exe",
                "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            },
            "Linux": "google-chrome"
        },
        "浏览器": {
            "Darwin": "Google Chrome",
            "Windows": {
                "exe": "chrome.exe",
                "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            },
            "Linux": "google-chrome"
        },
        "微信": {
            "Darwin": "WeChat",
            "Windows": {
                "exe": "WeChat.exe",
                "path": r"D:\tools\contact\Weixin.exe"
            },
            "Linux": "wechat"
        },
        "wechat": {
            "Darwin": "WeChat",
            "Windows": {
                "exe": "WeChat.exe",
                "path": r"D:\tools\contact\Weixin.exe"
            },
            "Linux": "wechat"
        },
        "记事本": {
            "Darwin": "TextEdit",
            "Windows": {
                "exe": "notepad.exe",
                "path": "notepad.exe"  # System app, no full path needed
            },
            "Linux": "gedit"
        },
        "vscode": {
            "Darwin": "Visual Studio Code",
            "Windows": {
                "exe": "Code.exe",
                "path": r"C:\Users\17994\AppData\Local\Programs\Microsoft VS Code"
            },
            "Linux": "code"
        },
        "终端": {
            "Darwin": "Terminal",
            "Windows": {
                "exe": "cmd.exe",
                "path": "cmd.exe"
            },
            "Linux": "gnome-terminal"
        },
        "terminal": {
            "Darwin": "Terminal",
            "Windows": {
                "exe": "cmd.exe",
                "path": "cmd.exe"
            },
            "Linux": "gnome-terminal"
        },
    }

    def _get_app_info(self, app_name: str) -> Any:
        """Get platform-specific app information"""
        system = platform.system()
        app_key = app_name.lower()

        if app_key in self.APP_MAP:
            return self.APP_MAP[app_key].get(system, app_name)
        return app_name

    def _run(self, app_name: str, action: str, **kwargs: Any) -> str:
        """执行应用程序控制"""
        try:
            app_info = self._get_app_info(app_name)

            if action == "open":
                return self._open_app(app_info)
            elif action == "close":
                return self._close_app(app_info)
            else:
                return f"Not supported action: {action}"
        except Exception as e:
            error_msg = f"failed to {action} app {app_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _open_app(self, app_info: Any) -> str:
        """打开应用程序"""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-a", app_info], check=True)
                return f"Opened app: {app_info}"

            elif system == "Windows":
                # app_info is a dict with 'exe' and 'path'
                if isinstance(app_info, dict):
                    path = app_info.get("path", app_info.get("exe"))
                else:
                    path = app_info

                # Try to open with full path
                subprocess.run(["start", "", path], shell=True, check=True)
                return f"Opened app: {path}"

            elif system == "Linux":
                subprocess.run([app_info], check=True)
                return f"Opened app: {app_info}"

            else:
                return f"Not supported operating system: {system}"

        except Exception as e:
            return f"Error opening app: {str(e)}"

    def _close_app(self, app_info: Any) -> str:
        """关闭应用程序"""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                script = f'tell application "{app_info}" to quit'
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    if "isn't running" in result.stderr or "not running" in result.stderr:
                        return f"App {app_info} is not running"
                    return f"Error closing app: {result.stderr}"
                return f"Closed app: {app_info}"

            elif system == "Windows":
                # app_info is a dict with 'exe'
                if isinstance(app_info, dict):
                    exe_name = app_info.get("exe")
                else:
                    exe_name = app_info if app_info.endswith(".exe") else f"{app_info}.exe"

                # Remove check=True to handle errors manually
                result = subprocess.run(
                    ["taskkill", "/IM", exe_name, "/F"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return f"Closed app: {exe_name}"
                elif result.returncode == 128:  # Process not found
                    return f"App {exe_name} is not running"
                else:
                    return f"Error closing app: {result.stderr}"

            elif system == "Linux":
                result = subprocess.run(
                    ["pkill", "-f", app_info],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return f"Closed app: {app_info}"
                elif result.returncode == 1:  # No process found
                    return f"App {app_info} is not running"
                else:
                    return f"Error closing app: {result.stderr}"

            else:
                return f"Not supported operating system: {system}"

        except Exception as e:
            return f"Error closing app: {str(e)}"


def app_control(**kwargs) -> BaseTool:
    """工厂函数：创建应用程序控制工具实例"""
    return AppControlTool(**kwargs)
