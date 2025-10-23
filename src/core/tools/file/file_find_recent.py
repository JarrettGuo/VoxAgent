#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_find_recent.py
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Type, List, Dict

from langchain_core.tools import BaseTool

from src.core.tools.base.file_operations_schemas import FileFindRecentSchema
from src.utils.logger import logger


class FileFindRecentTool(BaseTool):
    """最近修改文件查询工具 - 查找最近修改的文件"""

    name: str = "file_find_recent"
    description: str = (
        "查找最近N天内修改的文件。"
        "可以用来查找'这周修改的文件'、'最近编辑的文档'等。"
        "支持指定搜索目录和文件名过滤。"
    )
    args_schema: Type[FileFindRecentSchema] = FileFindRecentSchema

    def _run(
            self,
            directory: str = "~",
            days: int = 7,
            max_results: int = 20,
            file_pattern: str = None,
            **kwargs: Any
    ) -> str:
        """执行最近文件查询"""
        try:
            # 展开路径
            search_path = Path(directory).expanduser().resolve()

            if not search_path.exists():
                return f"Directory does not exist: {directory}"

            if not search_path.is_dir():
                return f"Path is not a directory: {directory}"

            # 计算时间阈值
            time_threshold = datetime.now() - timedelta(days=days)

            logger.info(f"Finding files modified in last {days} days")
            logger.info(f"Since: {time_threshold.strftime('%Y-%m-%d %H:%M')}")
            if file_pattern:
                logger.info(f"   Pattern: {file_pattern}")

            # 查找文件
            results = self._find_recent_files(
                search_path=search_path,
                time_threshold=time_threshold,
                file_pattern=file_pattern.lower() if file_pattern else None,
                max_results=max_results
            )

            if not results:
                msg = f"No files modified in the last {days} days"
                if file_pattern:
                    msg += f"matching '{file_pattern}'"
                return msg

            # 格式化输出
            return self._format_results(results, days, file_pattern)

        except Exception as e:
            error_msg = f"Failed to find recent files: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _find_recent_files(
            self,
            search_path: Path,
            time_threshold: datetime,
            file_pattern: str,
            max_results: int
    ) -> List[Dict[str, Any]]:
        """查找最近修改的文件"""
        results = []

        try:
            for item in search_path.rglob('*'):
                # 达到结果上限
                if len(results) >= max_results:
                    break

                try:
                    # 跳过目录和隐藏文件
                    if not item.is_file() or item.name.startswith('.'):
                        continue

                    # 跳过系统目录
                    if any(part.startswith('.') for part in item.parts):
                        continue

                    # 检查修改时间
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < time_threshold:
                        continue

                    # 检查文件名模式
                    if file_pattern and file_pattern not in item.name.lower():
                        continue

                    # 添加到结果
                    results.append({
                        "path": str(item),
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": mtime,
                    })

                except (PermissionError, OSError):
                    continue

        except Exception as e:
            logger.error(f"Error during search: {e}")

        # 按修改时间降序排序
        results.sort(key=lambda x: x['modified'], reverse=True)

        return results

    def _format_results(
            self,
            results: List[Dict[str, Any]],
            days: int,
            file_pattern: str
    ) -> str:
        """格式化查询结果"""
        pattern_str = f" matching '{file_pattern}'" if file_pattern else ""
        lines = [f"Found {len(results)} file(s) modified in the last {days} days{pattern_str}:\n"]

        for i, file_info in enumerate(results, 1):
            size_kb = file_info['size'] / 1024
            mtime = file_info['modified'].strftime('%Y-%m-%d %H:%M')

            lines.append(
                f"{i}. {file_info['name']}\n"
                f"   Path: {file_info['path']}\n"
                f"   Size: {size_kb:.1f} KB\n"
                f"   Modified: {mtime}\n"
            )

        return "\n".join(lines)


def file_find_recent(**kwargs) -> BaseTool:
    """工厂函数：创建最近文件查询工具实例"""
    return FileFindRecentTool(**kwargs)
