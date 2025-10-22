#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_write.py
"""

from pathlib import Path
from typing import Any, Type

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import FileWriteSchema
from src.utils.logger import logger


class FileWriteTool(BaseTool):
    """文件写入工具 - 覆盖写入文件内容"""

    name: str = "file_write"
    description: str = "写入内容到文件，会覆盖原有内容。如果文件不存在会自动创建"
    args_schema: Type[FileWriteSchema] = FileWriteSchema

    def _run(self, file_path: str, content: str, encoding: str = "utf-8", **kwargs: Any) -> str:
        """执行文件写入"""
        try:
            path = Path(file_path).expanduser()

            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件（覆盖模式）
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            logger.info(f"Wrote to file: {file_path} ({len(content)} chars)")
            return f"Successfully wrote {len(content)} characters to: {file_path}"

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to write file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg


def file_write(**kwargs) -> BaseTool:
    """工厂函数：创建文件写入工具实例"""
    return FileWriteTool(**kwargs)
