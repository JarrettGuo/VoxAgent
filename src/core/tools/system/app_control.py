#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : app_control.py
"""

import os
import platform
import subprocess
from typing import Any, Type, Dict

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import AppControlSchema
from src.utils.logger import logger


class AppControlTool(BaseTool):
    """应用程序控制工具 - 打开或关闭应用程序"""

    name: str = "app_control"
    description: str = "用于打开或关闭计算机上的应用程序。支持的操作：打开应用、关闭应用"
    args_schema: Type[AppControlSchema] = AppControlSchema

    # 多平台映射
    @staticmethod
    def _get_app_map() -> Dict[str, Dict[str, Any]]:
        """动态生成应用映射（避免在类定义时访问环境变量）"""
        system = platform.system()

        # Windows 路径
        if system == "Windows":
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))

            windows_chrome_path = os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe")
            windows_vscode_path = os.path.join(local_appdata, "Programs", "Microsoft VS Code", "Code.exe")
        else:
            windows_chrome_path = None
            windows_vscode_path = None

        return {
            "chrome": {
                "Darwin": "Google Chrome",
                "Windows": {
                    "exe": "chrome.exe",
                    "path": windows_chrome_path
                },
                "Linux": "google-chrome"
            },
            "浏览器": {
                "Darwin": "Google Chrome",
                "Windows": {
                    "exe": "chrome.exe",
                    "path": windows_chrome_path
                },
                "Linux": "google-chrome"
            },
            "safari": {
                "Darwin": "Safari",
                "Windows": None,
                "Linux": None
            },
            "微信": {
                "Darwin": "WeChat",
                "Windows": {
                    "exe": "WeChat.exe",
                    "path": r"C:\Program Files\Tencent\WeChat\WeChat.exe"  # 默认路径
                },
                "Linux": "wechat"
            },
            "wechat": {
                "Darwin": "WeChat",
                "Windows": {
                    "exe": "WeChat.exe",
                    "path": r"C:\Program Files\Tencent\WeChat\WeChat.exe"
                },
                "Linux": "wechat"
            },
            "记事本": {
                "Darwin": "TextEdit",
                "Windows": {
                    "exe": "notepad.exe",
                    "path": "notepad.exe"
                },
                "Linux": "gedit"
            },
            "notepad": {
                "Darwin": "TextEdit",
                "Windows": {
                    "exe": "notepad.exe",
                    "path": "notepad.exe"
                },
                "Linux": "gedit"
            },
            "vscode": {
                "Darwin": "Visual Studio Code",
                "Windows": {
                    "exe": "Code.exe",
                    "path": windows_vscode_path
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
            # macOS 特有应用
            "music": {
                "Darwin": "Music",
                "Windows": None,
                "Linux": None
            },
            "mail": {
                "Darwin": "Mail",
                "Windows": None,
                "Linux": None
            },
            "notes": {
                "Darwin": "Notes",
                "Windows": None,
                "Linux": None
            },
            "finder": {
                "Darwin": "Finder",
                "Windows": None,
                "Linux": None
            },
        }

    def _get_app_info(self, app_name: str) -> Any:
        """Get platform-specific app information"""
        system = platform.system()
        app_key = app_name.lower()

        app_map = self._get_app_map()

        if app_key in app_map:
            app_info = app_map[app_key].get(system)
            if app_info is None:
                raise ValueError(f"应用 '{app_name}' 在 {system} 平台上不可用")
            return app_info

        # 如果不在映射中，返回原始名称
        logger.warning(f"App '{app_name}' not in predefined map, using as-is")
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
                return f"不支持的操作: {action}，支持的操作: open, close"
        except ValueError as e:
            # 平台不支持的应用
            return str(e)
        except Exception as e:
            error_msg = f"执行 {action} 应用 {app_name} 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    def _open_app(self, app_info: Any) -> str:
        """打开应用程序"""
        system = platform.system()

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-a", app_info], check=True)
                return f"已打开应用: {app_info}"

            elif system == "Windows":
                # app_info is a dict with 'exe' and 'path'
                if isinstance(app_info, dict):
                    path = app_info.get("path", app_info.get("exe"))
                else:
                    path = app_info

                if not path:
                    return f"无法找到应用路径"

                # Try to open with full path
                subprocess.run(["start", "", path], shell=True, check=True)
                return f"已打开应用: {path}"

            elif system == "Linux":
                subprocess.run([app_info], check=True)
                return f"已打开应用: {app_info}"

            else:
                return f"不支持的操作系统: {system}"

        except subprocess.CalledProcessError as e:
            return f"打开应用失败: {str(e)}"
        except Exception as e:
            return f"打开应用时发生错误: {str(e)}"

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
                        return f"应用 {app_info} 未在运行"
                    return f"关闭应用失败: {result.stderr}"
                return f"已关闭应用: {app_info}"

            elif system == "Windows":
                # app_info is a dict with 'exe'
                if isinstance(app_info, dict):
                    exe_name = app_info.get("exe")
                else:
                    exe_name = app_info if app_info.endswith(".exe") else f"{app_info}.exe"

                if not exe_name:
                    return "无法确定应用的进程名"

                # Remove check=True to handle errors manually
                result = subprocess.run(
                    ["taskkill", "/IM", exe_name, "/F"],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return f"已关闭应用: {exe_name}"
                elif result.returncode == 128:  # Process not found
                    return f"应用 {exe_name} 未在运行"
                else:
                    return f"关闭应用失败: {result.stderr}"

            elif system == "Linux":
                result = subprocess.run(
                    ["pkill", "-f", app_info],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    return f"已关闭应用: {app_info}"
                elif result.returncode == 1:  # No process found
                    return f"应用 {app_info} 未在运行"
                else:
                    return f"关闭应用失败: {result.stderr}"

            else:
                return f"不支持的操作系统: {system}"

        except Exception as e:
            return f"关闭应用时发生错误: {str(e)}"


def app_control(**kwargs) -> BaseTool:
    """工厂函数：创建应用程序控制工具实例"""
    return AppControlTool(**kwargs)
