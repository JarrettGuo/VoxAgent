#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_file_create.py
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.tools import file_create
from src.utils.logger import logger


class TestFileCreateTool:
    """文件创建工具测试类"""

    def setup_method(self):
        """每个测试方法执行前调用"""
        self.tool = file_create()
        self.test_dir = tempfile.mkdtemp(prefix="voxagent_test_")
        logger.info(f"创建临时测试目录: {self.test_dir}")

    def teardown_method(self):
        """每个测试方法执行后调用"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            logger.info(f"清理临时测试目录: {self.test_dir}")

    def test_create_empty_file(self):
        """测试1: 创建空文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试1: 创建空文件")
        logger.info("=" * 60)

        file_path = os.path.join(self.test_dir, "empty_file.txt")

        result = self.tool._run(file_path=file_path)

        logger.info(f"结果: {result}")

        # 验证文件是否存在
        assert os.path.exists(file_path), "文件未创建"

        # 验证文件内容为空
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "", "文件内容不为空"

        logger.info("测试通过: 成功创建空文件")

    def test_create_file_with_content(self):
        """测试2: 创建包含内容的文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 创建包含内容的文件")
        logger.info("=" * 60)

        file_path = os.path.join(self.test_dir, "content_file.txt")
        test_content = "Hello, VoxAgent!\nThis is a test file."

        result = self.tool._run(
            file_path=file_path,
            content=test_content
        )

        logger.info(f"结果: {result}")

        # 验证文件是否存在
        assert os.path.exists(file_path), "文件未创建"

        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == test_content, "文件内容不匹配"

        logger.info("测试通过: 成功创建包含内容的文件")

    def test_create_file_in_nested_directory(self):
        """测试3: 在嵌套目录中创建文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 在嵌套目录中创建文件")
        logger.info("=" * 60)

        # 使用不存在的嵌套目录
        nested_path = os.path.join(
            self.test_dir,
            "level1",
            "level2",
            "level3",
            "nested_file.txt"
        )

        result = self.tool._run(
            file_path=nested_path,
            content="File in nested directory"
        )

        logger.info(f"结果: {result}")

        # 验证文件是否存在
        assert os.path.exists(nested_path), "嵌套目录中的文件未创建"

        # 验证父目录是否自动创建
        assert os.path.exists(os.path.dirname(nested_path)), "父目录未自动创建"

        logger.info("测试通过: 成功在嵌套目录中创建文件")

    def test_create_different_file_types(self):
        """测试4: 创建不同类型的文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试4: 创建不同类型的文件")
        logger.info("=" * 60)

        test_files = [
            ("test.py", "#!/usr/bin/env python\nprint('Hello')"),
            ("test.md", "# Markdown File\nThis is a test."),
            ("test.json", '{"key": "value"}'),
            ("test.yaml", "name: test\nvalue: 123"),
        ]

        for filename, content in test_files:
            file_path = os.path.join(self.test_dir, filename)
            result = self.tool._run(file_path=file_path, content=content)

            logger.info(f"创建 {filename}: {result}")

            # 验证文件存在
            assert os.path.exists(file_path), f"{filename} 未创建"

            # 验证内容
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            assert saved_content == content, f"{filename} 内容不匹配"

        logger.info("测试通过: 成功创建不同类型的文件")

    def test_create_file_with_chinese_content(self):
        """测试5: 创建包含中文内容的文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试5: 创建包含中文内容的文件")
        logger.info("=" * 60)

        file_path = os.path.join(self.test_dir, "chinese_file.txt")
        chinese_content = "你好，世界！\n这是一个测试文件。\n支持中文内容。"

        result = self.tool._run(
            file_path=file_path,
            content=chinese_content
        )

        logger.info(f"结果: {result}")

        # 验证文件是否存在
        assert os.path.exists(file_path), "文件未创建"

        # 验证中文内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == chinese_content, "中文内容不匹配"

        logger.info("测试通过: 成功创建包含中文内容的文件")

    def test_create_existing_file(self):
        """测试6: 尝试创建已存在的文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试6: 尝试创建已存在的文件")
        logger.info("=" * 60)

        file_path = os.path.join(self.test_dir, "existing_file.txt")

        # 第一次创建
        result1 = self.tool._run(
            file_path=file_path,
            content="Original content"
        )
        logger.info(f"第一次创建: {result1}")

        # 第二次创建（应该失败）
        result2 = self.tool._run(
            file_path=file_path,
            content="New content"
        )
        logger.info(f"第二次创建: {result2}")

        # 验证返回了警告信息
        assert "already exists" in result2.lower(), "未正确处理已存在的文件"

        # 验证原内容未被覆盖
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "Original content", "原文件内容被修改"

        logger.info("测试通过: 正确处理已存在的文件")

    def test_create_file_with_tilde_path(self):
        """测试7: 使用波浪号路径创建文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试7: 使用波浪号路径创建文件")
        logger.info("=" * 60)

        # 使用相对于用户主目录的路径
        file_path = "~/voxagent_test_tilde.txt"

        try:
            result = self.tool._run(
                file_path=file_path,
                content="Test with tilde path"
            )

            logger.info(f"结果: {result}")

            # 验证文件是否存在
            expanded_path = Path(file_path).expanduser()
            assert expanded_path.exists(), "文件未创建"

            logger.info("测试通过: 成功处理波浪号路径")

        finally:
            # 清理测试文件
            expanded_path = Path(file_path).expanduser()
            if expanded_path.exists():
                expanded_path.unlink()
                logger.info(f"清理测试文件: {expanded_path}")

    def test_create_large_file(self):
        """测试8: 创建大文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试8: 创建大文件")
        logger.info("=" * 60)

        file_path = os.path.join(self.test_dir, "large_file.txt")

        # 生成约 1MB 的内容
        large_content = "A" * 1024 * 1024  # 1MB

        result = self.tool._run(
            file_path=file_path,
            content=large_content
        )

        logger.info(f"📋 结果: {result}")

        # 验证文件是否存在
        assert os.path.exists(file_path), "大文件未创建"

        # 验证文件大小
        file_size = os.path.getsize(file_path)
        assert file_size >= 1024 * 1024, f"文件大小不符: {file_size} bytes"

        logger.info(f"测试通过: 成功创建大文件 ({file_size / 1024 / 1024:.2f} MB)")

    def test_create_file_with_special_characters(self):
        """测试9: 创建包含特殊字符的文件名"""
        logger.info("\n" + "=" * 60)
        logger.info("测试9: 创建包含特殊字符的文件名")
        logger.info("=" * 60)

        # 注意：某些特殊字符在不同操作系统中可能不被允许
        # 这里只测试常见的安全字符
        special_files = [
            "file-with-dash.txt",
            "file_with_underscore.txt",
            "file.with.dots.txt",
            "file (with parentheses).txt",
        ]

        for filename in special_files:
            file_path = os.path.join(self.test_dir, filename)
            result = self.tool._run(
                file_path=file_path,
                content=f"Content of {filename}"
            )

            # 验证文件存在
            assert os.path.exists(file_path), f"{filename} 未创建"

        logger.info("测试通过: 成功创建包含特殊字符的文件名")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "-s"])
