#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_list.py
"""
# src/core/tools/file/file_list.py
from datetime import datetime
from pathlib import Path
from typing import Any, Type, List, Dict

from langchain_core.tools import BaseTool

from src.core.tools.base.file_operations_schemas import FileListSchema
from src.utils.logger import logger


class FileListTool(BaseTool):
    """目录列表工具 - 列出指定目录的文件和子目录"""

    name: str = "file_list"
    description: str = (
        "列出指定目录下的文件和子目录。"
        "可以查看桌面、文档等目录的内容，支持按名称、时间、大小排序。"
    )
    args_schema: Type[FileListSchema] = FileListSchema

    def _run(
            self,
            directory: str = "~",
            show_hidden: bool = False,
            sort_by: str = "name",
            **kwargs: Any
    ) -> str:
        """执行目录列表"""
        try:
            # 展开路径
            dir_path = Path(directory).expanduser().resolve()

            if not dir_path.exists():
                return f"Directory does not exist: {directory}"

            if not dir_path.is_dir():
                return f"Path is not a directory: {directory}"

            logger.info(f"Listing contents of: {dir_path}")

            # 获取文件列表
            items = []
            for item in dir_path.iterdir():
                # 跳过隐藏文件（如果不显示）
                if not show_hidden and item.name.startswith('.'):
                    continue

                try:
                    items.append(self._get_item_info(item))
                except Exception as e:
                    logger.debug(f"Error getting info for {item}: {e}")
                    continue

            # 排序
            items = self._sort_items(items, sort_by)

            # 格式化输出
            return self._format_listing(dir_path, items)

        except PermissionError:
            error_msg = f"Permission denied: {directory}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Failed to list directory: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _get_item_info(self, path: Path) -> Dict[str, Any]:
        """获取文件/目录信息"""
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "is_dir": path.is_dir(),
            "size": stat.st_size if path.is_file() else 0,
            "modified": datetime.fromtimestamp(stat.st_mtime),
        }

    def _sort_items(self, items: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """排序文件列表"""
        if sort_by == "modified":
            return sorted(items, key=lambda x: x['modified'], reverse=True)
        elif sort_by == "size":
            return sorted(items, key=lambda x: x['size'], reverse=True)
        else:  # name
            # 目录在前，然后按名称排序
            return sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower()))

    def _format_listing(self, directory: Path, items: List[Dict[str, Any]]) -> str:
        """格式化目录列表"""
        lines = [f"Contents of {directory}:\n"]
        lines.append(f"Total: {len(items)} item(s)\n")

        for item in items:
            icon = "📁" if item['is_dir'] else "📄"
            name = item['name']
            mtime = item['modified'].strftime('%Y-%m-%d %H:%M')

            if item['is_dir']:
                lines.append(f"{icon} {name}/\n   Modified: {mtime}\n")
            else:
                size_kb = item['size'] / 1024
                lines.append(
                    f"{icon} {name}\n"
                    f"   Size: {size_kb:.1f} KB | Modified: {mtime}\n"
                )

        return "\n".join(lines)


def file_list(**kwargs) -> BaseTool:
    """工厂函数：创建目录列表工具实例"""
    return FileListTool(**kwargs)
