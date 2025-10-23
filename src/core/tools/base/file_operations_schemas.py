#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : file_operations_schemas.py
"""
from pydantic import Field, BaseModel


class FileReadSchema(BaseModel):
    """文件读取参数"""
    file_path: str = Field(description="要读取的文件路径")
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8")


class FileCreateSchema(BaseModel):
    """文件创建参数"""
    file_path: str = Field(description="要创建的文件路径，例如：/Users/xxx/document.txt")
    content: str = Field(default="", description="文件初始内容（可选）")


class FileWriteSchema(BaseModel):
    """文件写入参数"""
    file_path: str = Field(description="要写入的文件路径")
    content: str = Field(description="要写入的内容")
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8")


class FileAppendSchema(BaseModel):
    """文件追加参数"""
    file_path: str = Field(description="要追加内容的文件路径")
    content: str = Field(description="要追加的内容")
    encoding: str = Field(default="utf-8", description="文件编码，默认 utf-8")


class FileDeleteSchema(BaseModel):
    """文件删除参数"""
    file_path: str = Field(description="要删除的文件路径")


class FileSearchSchema(BaseModel):
    """文件搜索参数"""
    query: str = Field(description="要搜索的文件名关键词（支持模糊匹配）")
    search_path: str = Field(
        default="~",
        description="搜索路径，默认为用户主目录。可以指定如 ~/Desktop, ~/Documents 等"
    )
    max_depth: int = Field(
        default=3,
        description="搜索深度，默认为3层。值越大搜索越深但速度越慢"
    )
    max_results: int = Field(
        default=10,
        description="最多返回的结果数量，默认10个"
    )
    days_ago: int = Field(
        default=None,
        description="只搜索最近N天内修改的文件（可选）"
    )


class FileListSchema(BaseModel):
    """目录列表参数"""
    directory: str = Field(
        default="~",
        description="要列出内容的目录路径，如 ~/Desktop, ~/Documents"
    )
    show_hidden: bool = Field(
        default=False,
        description="是否显示隐藏文件"
    )
    sort_by: str = Field(
        default="name",
        description="排序方式: name(名称), modified(修改时间), size(大小)"
    )


class FileFindRecentSchema(BaseModel):
    """最近修改文件参数"""
    directory: str = Field(
        default="~",
        description="搜索目录，默认为用户主目录"
    )
    days: int = Field(
        default=7,
        description="查找最近N天内修改的文件，默认7天"
    )
    max_results: int = Field(
        default=20,
        description="最多返回的结果数量，默认20个"
    )
    file_pattern: str = Field(
        default=None,
        description="文件名过滤模式（可选），如 '报告', '.pdf' 等"
    )
