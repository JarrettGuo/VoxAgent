#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_create.py
"""

from pathlib import Path
from typing import Any, Type

from langchain_core.tools import BaseTool

from src.core.tools.base.file_operations_schemas import FileCreateSchema
from src.utils.logger import logger


class FileCreateTool(BaseTool):
    """文件创建工具 - 创建新文件"""

    name: str = "file_create"
    description: str = "用于创建新文件。可以创建文本文件、代码文件等。支持指定文件路径和初始内容"
    args_schema: Type[FileCreateSchema] = FileCreateSchema

    def _run(self, file_path: str, content: str = "", **kwargs: Any) -> str:
        """执行文件创建"""
        try:
            logger.info(f"创建文件: {file_path}")

            # 转换为 Path 对象
            path = Path(file_path).expanduser()

            # 检查文件是否已存在
            if path.exists():
                return f"File already exists: {file_path}"

            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 创建文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"File created: {file_path}")
            return f"File created: {file_path}"

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to create file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg


def file_create(**kwargs) -> BaseTool:
    """工厂函数：创建文件创建工具实例"""
    return FileCreateTool(**kwargs)
