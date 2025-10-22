#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_read.py
"""

from pathlib import Path
from typing import Any, Type

from langchain_core.tools import BaseTool

from src.core.tools.base.file_operations_schemas import FileReadSchema
from src.utils.logger import logger


class FileReadTool(BaseTool):
    """文件读取工具 - 读取文件内容"""

    name: str = "file_read"
    description: str = "读取文件的完整内容。支持文本文件，返回文件的全部文本内容"
    args_schema: Type[FileReadSchema] = FileReadSchema

    def _run(self, file_path: str, encoding: str = "utf-8", **kwargs: Any) -> str:
        """执行文件读取"""
        try:
            path = Path(file_path).expanduser()

            if not path.exists():
                return f"File not found: {file_path}"

            if not path.is_file():
                return f"Path is not a file: {file_path}"

            # 读取文件
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()

            return content

        except UnicodeDecodeError:
            error_msg = f"Cannot decode file with {encoding} encoding: {file_path}"
            logger.error(error_msg)
            return error_msg

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to read file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg


def file_read(**kwargs) -> BaseTool:
    """工厂函数：创建文件读取工具实例"""
    return FileReadTool(**kwargs)
