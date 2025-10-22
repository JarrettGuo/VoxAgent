#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_append.py
"""

from pathlib import Path
from typing import Any, Type

from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import FileAppendSchema
from src.utils.logger import logger


class FileAppendTool(BaseTool):
    """文件追加工具 - 在文件末尾追加内容"""

    name: str = "file_append"
    description: str = "在文件末尾追加内容，不会覆盖原有内容。如果文件不存在会自动创建"
    args_schema: Type[FileAppendSchema] = FileAppendSchema

    def _run(self, file_path: str, content: str, encoding: str = "utf-8", **kwargs: Any) -> str:
        """执行文件追加"""
        try:
            path = Path(file_path).expanduser()

            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 追加到文件
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)

            logger.info(f"Appended to file: {file_path} ({len(content)} chars)")
            return f"Successfully appended {len(content)} characters to: {file_path}"

        except PermissionError:
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to append to file {file_path}: {str(e)}"
            logger.error(error_msg)
            return error_msg


def file_append(**kwargs) -> BaseTool:
    """工厂函数：创建文件追加工具实例"""
    return FileAppendTool(**kwargs)
