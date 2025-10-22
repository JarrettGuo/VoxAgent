#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_delete.py
"""

from pathlib import Path
from typing import Any, Type

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import FileDeleteSchema
from src.utils.logger import logger


class FileDeleteTool(BaseTool):
    """文件删除工具 - 删除指定文件"""

    name: str = "file_delete"
    description: str = "删除指定的文件。注意：删除操作不可恢复，请谨慎使用"
    args_schema: Type[FileDeleteSchema] = FileDeleteSchema

    def _run(self, file_path: str, **kwargs: Any) -> str:
        """执行文件删除"""
        try:
            path = Path(file_path).expanduser()

            if not path.exists():
                return f"File not found: {file_path}"

            if not path.is_file():
                return f"Path is not a file: {file_path}"

            # 删除文件
            path.unlink()

            logger.info(f"Deleted file: {file_path}")
            return f"Successfully deleted: {file_path}"

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to delete file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg


def file_delete(**kwargs) -> BaseTool:
    """工厂函数：创建文件删除工具实例"""
    return FileDeleteTool(**kwargs)
