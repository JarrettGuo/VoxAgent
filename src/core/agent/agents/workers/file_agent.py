from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_core.tools import BaseTool

from src.core.agent.agents.base_agent import BaseAgent
from src.core.agent.entities.agent_prompts import FILE_MANAGEMENT_AGENT_PROMPT
from src.utils.logger import logger


class FileManagementAgent(
    BaseAgent,
    agent_type="file",
    priority=80,  # High priority - frequently used
    platforms=["darwin", "linux", "windows"],
    required_tools=["file_create", "file_read", "file_write"],
):
    agent_name = "file_agent"
    agent_description = (
        "负责所有文件系统操作，包括：创建、读取、写入、追加、删除文件；"
        "搜索文件、列出目录内容、查找最近修改的文件。"
        "适用场景：创建文档、编辑配置文件、整理文件、查找文件等"
    )
    agent_system_prompt = """你是一个专业的文件管理助手，负责帮助用户完成文件操作任务。"""

    def __init__(self):
        super().__init__()
        # 定义常用目录映射
        self.common_dirs = {
            "桌面": self._get_desktop_path(),
            "desktop": self._get_desktop_path(),
            "文档": self._get_documents_path(),
            "documents": self._get_documents_path(),
            "下载": self._get_downloads_path(),
            "downloads": self._get_downloads_path(),
            "图片": self._get_pictures_path(),
            "pictures": self._get_pictures_path(),
            "音乐": self._get_music_path(),
            "music": self._get_music_path(),
            "视频": self._get_videos_path(),
            "videos": self._get_videos_path(),
        }

    @classmethod
    def generate_system_prompt(cls, tools: List[BaseTool]) -> str:
        """动态生成文件管理 Agent 的系统 prompt"""

        # 动态生成工具列表
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")

        tools_section = "\n".join(tool_descriptions)

        prompt_template = FILE_MANAGEMENT_AGENT_PROMPT

        return prompt_template.format(tools_section=tools_section)

    async def read_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """读取文件内容"""
        try:
            # 解析路径
            resolved_path = self._resolve_path(file_path)

            # 文件不存在
            if not resolved_path.exists():
                suggestion = self._suggest_similar_files(resolved_path)
                error_msg = f"文件不存在: {file_path}"

                if suggestion:
                    error_msg += f"\n{suggestion}"

                return {
                    "success": False,
                    "error": error_msg,
                    "status": "failed",
                    "suggestion": suggestion
                }

            # 不是文件
            if not resolved_path.is_file():
                return {
                    "success": False,
                    "error": f"路径不是文件: {file_path}",
                    "status": "failed"
                }

            # 读取文件
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "result": content,
                "file_path": str(resolved_path),
                "status": "completed"
            }

        except PermissionError:
            return {
                "success": False,
                "error": f"无权限访问文件: {file_path}",
                "status": "failed"
            }

        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"文件编码错误，无法读取: {file_path}",
                "status": "failed"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"读取文件失败: {str(e)}",
                "status": "failed"
            }

    def _suggest_similar_files(self, path: Path) -> Optional[str]:
        """建议相似的文件名"""
        from difflib import get_close_matches

        try:
            parent = path.parent
            if not parent.exists():
                return None

            # 获取目录下所有文件
            files = [f.name for f in parent.iterdir() if f.is_file()]

            if not files:
                return None

            # 找相似的文件名
            matches = get_close_matches(path.name, files, n=3, cutoff=0.5)

            if matches:
                return f"您可能想找：{', '.join(matches)}"

            return None

        except Exception as e:
            logger.warning(f"Failed to suggest similar files: {e}")
            return None

    def _resolve_path(self, file_path: str) -> Path:
        """
        解析文件路径
        支持：
        1. 绝对路径: /Users/xxx/file.txt
        2. 相对路径: ./file.txt, ../file.txt
        3. 用户目录: ~/file.txt
        4. 特殊目录: 桌面/file.txt, Desktop/file.txt
        """
        # 1. 去除首尾空格
        file_path = file_path.strip()

        # 2. 检查是否以特殊目录名开头
        for dir_name, dir_path in self.common_dirs.items():
            if file_path.lower().startswith(dir_name.lower()):
                # 替换特殊目录名为实际路径
                # 例如："桌面/test.txt" → "/Users/xxx/Desktop/test.txt"
                relative_part = file_path[len(dir_name):].lstrip("/\\")
                return dir_path / relative_part

        # 3. 使用 Path 处理其他情况
        path = Path(file_path)

        # 4. 展开用户目录 (~)
        path = path.expanduser()

        # 5. 如果是相对路径，转换为绝对路径
        if not path.is_absolute():
            path = Path.cwd() / path

        # 6. 规范化路径（解析 .. 和 .）
        path = path.resolve()

        return path

    @staticmethod
    def _get_desktop_path() -> Path:
        """获取桌面路径（跨平台）"""
        home = Path.home()

        # macOS 和 Linux
        desktop = home / "Desktop"
        if desktop.exists():
            return desktop

        # Windows
        desktop = home / "桌面"
        if desktop.exists():
            return desktop

        # 默认返回 Desktop
        return home / "Desktop"

    @staticmethod
    def _get_documents_path() -> Path:
        """获取文档路径（跨平台）"""
        home = Path.home()

        # macOS 和 Linux
        docs = home / "Documents"
        if docs.exists():
            return docs

        # Windows 中文系统
        docs = home / "文档"
        if docs.exists():
            return docs

        return home / "Documents"

    @staticmethod
    def _get_downloads_path() -> Path:
        """获取下载路径（跨平台）"""
        home = Path.home()

        # macOS 和 Linux
        downloads = home / "Downloads"
        if downloads.exists():
            return downloads

        # Windows 中文系统
        downloads = home / "下载"
        if downloads.exists():
            return downloads

        return home / "Downloads"

    @staticmethod
    def _get_pictures_path() -> Path:
        """获取图片路径"""
        home = Path.home()

        pictures = home / "Pictures"
        if pictures.exists():
            return pictures

        pictures = home / "图片"
        if pictures.exists():
            return pictures

        return home / "Pictures"

    @staticmethod
    def _get_music_path() -> Path:
        """获取音乐路径"""
        home = Path.home()

        music = home / "Music"
        if music.exists():
            return music

        music = home / "音乐"
        if music.exists():
            return music

        return home / "Music"

    @staticmethod
    def _get_videos_path() -> Path:
        """获取视频路径"""
        home = Path.home()

        videos = home / "Videos"
        if videos.exists():
            return videos

        videos = home / "视频"
        if videos.exists():
            return videos

        return home / "Videos"
