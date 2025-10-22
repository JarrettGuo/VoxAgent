#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_search.py
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Type, List, Dict

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import FileSearchSchema
from src.utils.logger import logger


class FileSearchTool(BaseTool):
    """文件搜索工具 - 根据文件名模糊搜索文件"""

    name: str = "file_search"
    description: str = (
        "根据文件名关键词搜索文件。支持模糊匹配，可以指定搜索路径、搜索深度和时间范围。"
        "例如：搜索桌面上包含'报告'的文件，搜索最近一周修改的文件等。"
    )
    args_schema: Type[FileSearchSchema] = FileSearchSchema

    def _run(
            self,
            query: str,
            search_path: str = "~",
            max_depth: int = 3,
            max_results: int = 10,
            days_ago: int = None,
            **kwargs: Any
    ) -> str:
        """执行文件搜索"""
        try:
            # 展开路径
            search_path = Path(search_path).expanduser().resolve()

            if not search_path.exists():
                return f"Search path does not exist: {search_path}"

            if not search_path.is_dir():
                return f"Search path is not a directory: {search_path}"

            # 计算时间范围
            time_threshold = None
            if days_ago is not None:
                time_threshold = datetime.now() - timedelta(days=days_ago)
                logger.info(f"Only files modified after {time_threshold.strftime('%Y-%m-%d')}")

            # 搜索文件
            results = self._search_files(
                search_path=search_path,
                query=query.lower(),
                max_depth=max_depth,
                max_results=max_results,
                time_threshold=time_threshold,
                current_depth=0
            )

            if not results:
                return f"No files found matching '{query}' in {search_path}"

            # 格式化输出
            return self._format_results(results, query)

        except Exception as e:
            error_msg = f"Failed to search files: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _search_files(
            self,
            search_path: Path,
            query: str,
            max_depth: int,
            max_results: int,
            time_threshold: datetime,
            current_depth: int
    ) -> List[Dict[str, Any]]:
        """递归搜索文件"""
        results = []

        try:
            # 检查深度限制
            if current_depth > max_depth:
                return results

            # 遍历目录
            for item in search_path.iterdir():
                # 已达到结果上限
                if len(results) >= max_results:
                    break

                try:
                    # 跳过隐藏文件和系统文件
                    if item.name.startswith('.'):
                        continue

                    # 如果是文件
                    if item.is_file():
                        # 检查文件名是否匹配
                        if query in item.name.lower():
                            # 检查修改时间
                            if time_threshold:
                                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                                if mtime < time_threshold:
                                    continue

                            # 添加到结果
                            results.append(self._get_file_info(item))

                    # 如果是目录，递归搜索
                    elif item.is_dir():
                        # 跳过一些常见的大型目录
                        skip_dirs = {
                            'node_modules', '.git', '__pycache__',
                            'venv', '.venv', 'Library', 'Applications'
                        }
                        if item.name in skip_dirs:
                            continue

                        sub_results = self._search_files(
                            search_path=item,
                            query=query,
                            max_depth=max_depth,
                            max_results=max_results - len(results),
                            time_threshold=time_threshold,
                            current_depth=current_depth + 1
                        )
                        results.extend(sub_results)

                except PermissionError:
                    # 跳过无权限的文件/目录
                    continue
                except Exception as e:
                    logger.debug(f"Error processing {item}: {e}")
                    continue

        except PermissionError:
            logger.debug(f"Permission denied: {search_path}")
        except Exception as e:
            logger.error(f"Error searching in {search_path}: {e}")

        return results

    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息"""
        stat = file_path.stat()
        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime),
        }

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        lines = [f"Found {len(results)} file(s) matching '{query}':\n"]

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


def file_search(**kwargs) -> BaseTool:
    """工厂函数：创建文件搜索工具实例"""
    return FileSearchTool(**kwargs)
