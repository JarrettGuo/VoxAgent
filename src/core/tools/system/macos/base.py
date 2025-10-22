#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : base.py
"""

import platform
import subprocess
from abc import ABC

from langchain_core.tools import BaseTool
from pydantic import Field

from src.utils.logger import logger


class AppleScriptError(Exception):
    """AppleScript 执行错误"""
    pass


class MacOSBaseTool(BaseTool, ABC):
    """macOS 工具基类 - 提供 AppleScript 执行支持"""

    # 是否仅支持 macOS
    macos_only: bool = Field(default=True, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 检查操作系统
        if self.macos_only and not self._is_macos():
            logger.warning(f"{self.name} is only supported on macOS")

    @staticmethod
    def _is_macos() -> bool:
        """检查是否为 macOS 系统"""
        return platform.system() == "Darwin"

    def _execute_applescript(
            self,
            script: str,
            timeout: int = 30
    ) -> str:
        """执行 AppleScript 并返回结果"""
        if not self._is_macos():
            raise AppleScriptError("AppleScript only supported on macOS")

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )

            output = result.stdout.strip()
            return output

        except subprocess.TimeoutExpired:
            error_msg = f"AppleScript execution timeout after {timeout}s"
            logger.error(error_msg)
            raise AppleScriptError(error_msg)

        except subprocess.CalledProcessError as e:
            error_msg = f"AppleScript execution failed: {e.stderr}"
            logger.error(error_msg)
            raise AppleScriptError(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise AppleScriptError(error_msg)

    def _format_error_response(self, error: Exception) -> str:
        """格式化错误响应"""
        if isinstance(error, AppleScriptError):
            return f"Operation failed: {str(error)}"
        return f"Unexpected error: {str(error)}"

    def _ensure_app_running(self, app_name: str) -> bool:
        """确保应用正在运行"""
        script = f'''
        tell application "{app_name}"
            if not running then
                launch
                delay 2
            end if
            return running
        end tell
        '''

        try:
            result = self._execute_applescript(script)
            return result.lower() == "true"
        except AppleScriptError:
            return False
