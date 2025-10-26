import platform
from abc import ABC

import win32com
from langchain_core.tools import BaseTool
from pydantic import Field

from src.core.tools.music import MusicPlayer
from src.utils.logger import logger

class Windowsautomationerror(Exception):
    """Windows automation execution error"""
    pass


class WindowsBaseTool(BaseTool, ABC):
    """Windows tool base class - provides COM automation support"""

    windows_only: bool = Field(default=True, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.windows_only and not self._is_windows():
            logger.warning(f"{self.name} is only supported on Windows")
        if win32com is None:
            logger.error("pywin32 is not installed. Install it with: pip install pywin32")

    @staticmethod
    def _is_windows() -> bool:
        """Check if running on Windows"""
        return platform.system() == "Windows"

    def _format_error_response(self, error: Exception) -> str:
        """Format error response"""
        if isinstance(error, Windowsautomationerror):
            return f"Operation failed: {str(error)}"
        return f"Unexpected error: {str(error)}"


class BaseMusicTool(BaseTool, ABC):
    """基础音乐工具类"""

    player: MusicPlayer = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = MusicPlayer.get_instance()
