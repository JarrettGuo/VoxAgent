# tests/tools/test_file_operations.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : test_file_operations.py
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.core.tools import tool_registry
from src.utils.logger import logger


class TestFileOperations:
    """文件操作工具测试类 - 核心功能测试"""

    def setup_method(self):
        """每个测试方法执行前调用"""
        self.test_dir = tempfile.mkdtemp(prefix="voxagent_fileops_")
        logger.info(f"创建临时测试目录: {self.test_dir}")

    def teardown_method(self):
        """每个测试方法执行后调用"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            logger.info(f"清理临时测试目录: {self.test_dir}")

    def test_file_create(self):
        """测试 file_create：创建文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_create")
        logger.info("=" * 60)

        test_file = os.path.join(self.test_dir, "create_test.txt")
        test_content = "Hello, VoxAgent!"

        # 使用新的 registry API
        tool = tool_registry.get_tool("file_create")
        result = tool._run(file_path=test_file, content=test_content)

        logger.info(f"结果: {result}")

        # 验证文件创建
        assert os.path.exists(test_file), "文件未创建"

        # 验证内容
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == test_content, "文件内容不匹配"

        logger.info("测试通过: file_create")

    def test_file_read(self):
        """测试 file_read：读取文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_read")
        logger.info("=" * 60)

        # 准备测试文件
        test_file = os.path.join(self.test_dir, "read_test.txt")
        test_content = "Hello, VoxAgent!\n这是测试内容。"

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        # 读取文件
        tool = tool_registry.get_tool("file_read")
        result = tool._run(file_path=test_file)

        logger.info(f"结果: {result}")

        # 验证
        assert result == test_content, "读取的内容不匹配"
        logger.info("测试通过: file_read")

    def test_file_write(self):
        """测试 file_write：写入文件（覆盖）"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_write")
        logger.info("=" * 60)

        test_file = os.path.join(self.test_dir, "write_test.txt")

        # 先写入原始内容
        original_content = "Original content"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 使用 file_write 覆盖
        new_content = "New content"
        tool = tool_registry.get_tool("file_write")
        result = tool._run(file_path=test_file, content=new_content)

        logger.info(f"结果: {result}")

        # 验证内容已被覆盖
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == new_content, "文件未被正确覆盖"
        assert content != original_content, "原内容未被覆盖"

        logger.info("测试通过: file_write")

    def test_file_append(self):
        """测试 file_append：追加内容"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_append")
        logger.info("=" * 60)

        test_file = os.path.join(self.test_dir, "append_test.txt")

        # 创建初始文件
        original_content = "Line 1\n"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # 追加内容
        append_content = "Line 2\n"
        tool = tool_registry.get_tool("file_append")
        result = tool._run(file_path=test_file, content=append_content)

        logger.info(f"结果: {result}")

        # 验证内容
        with open(test_file, 'r', encoding='utf-8') as f:
            final_content = f.read()

        expected_content = original_content + append_content
        assert final_content == expected_content, "追加内容不正确"

        logger.info("测试通过: file_append")

    def test_file_delete(self):
        """测试 file_delete：删除文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_delete")
        logger.info("=" * 60)

        # 创建测试文件
        test_file = os.path.join(self.test_dir, "delete_test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This file will be deleted")

        # 确认文件存在
        assert os.path.exists(test_file), "测试文件未创建"

        # 删除文件
        tool = tool_registry.get_tool("file_delete")
        result = tool._run(file_path=test_file)

        logger.info(f"结果: {result}")

        # 验证文件已删除
        assert not os.path.exists(test_file), "文件未被删除"
        logger.info("测试通过: file_delete")

    def test_file_search(self):
        """测试 file_search：搜索文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_search")
        logger.info("=" * 60)

        # 创建测试文件
        files = [
            "report_2024.txt",
            "meeting_notes.txt",
            "report_draft.txt",
        ]

        for filename in files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"Content of {filename}")

        # 搜索包含 "report" 的文件
        tool = tool_registry.get_tool("file_search")
        result = tool._run(
            query="report",
            search_path=self.test_dir,
            max_depth=1
        )

        logger.info(f"结果:\n{result}")

        # 验证结果
        assert "report_2024.txt" in result, "应该找到 report_2024.txt"
        assert "report_draft.txt" in result, "应该找到 report_draft.txt"
        assert "meeting_notes.txt" not in result, "不应该找到 meeting_notes.txt"

        logger.info("测试通过: file_search")

    def test_file_list(self):
        """测试 file_list：列出目录内容"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_list")
        logger.info("=" * 60)

        # 创建测试文件和目录
        files = ["file1.txt", "file2.txt"]
        subdirs = ["subdir1"]

        for filename in files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"Content of {filename}")

        for dirname in subdirs:
            os.makedirs(os.path.join(self.test_dir, dirname), exist_ok=True)

        # 列出目录内容
        tool = tool_registry.get_tool("file_list")
        result = tool._run(directory=self.test_dir)

        logger.info(f"结果:\n{result}")

        # 验证所有文件和目录都在列表中
        for filename in files:
            assert filename in result, f"应该列出 {filename}"
        for dirname in subdirs:
            assert dirname in result, f"应该列出目录 {dirname}"

        logger.info("测试通过: file_list")

    def test_file_find_recent(self):
        """测试 file_find_recent：查找最近修改的文件"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 file_find_recent")
        logger.info("=" * 60)

        # 创建新旧文件
        old_file = os.path.join(self.test_dir, "old_file.txt")
        recent_file = os.path.join(self.test_dir, "recent_file.txt")

        with open(old_file, 'w') as f:
            f.write("Old content")
        with open(recent_file, 'w') as f:
            f.write("Recent content")

        # 设置旧文件的时间为30天前
        old_time = (datetime.now() - timedelta(days=30)).timestamp()
        os.utime(old_file, (old_time, old_time))

        # 查找最近7天的文件
        tool = tool_registry.get_tool("file_find_recent")
        result = tool._run(
            directory=self.test_dir,
            days=7
        )

        logger.info(f"结果:\n{result}")

        # 验证只找到最近的文件
        assert "recent_file.txt" in result, "应该找到最近的文件"
        assert "old_file.txt" not in result, "不应该找到旧文件"

        logger.info("测试通过: file_find_recent")

    def test_create_file_on_desktop(self):
        """✨ 测试在桌面创建 test.doc 文件（不删除）"""
        logger.info("\n" + "=" * 60)
        logger.info("测试在桌面创建 test.doc")
        logger.info("=" * 60)

        # 获取桌面路径
        desktop_path = Path.home() / "Desktop"
        test_file = desktop_path / "test.doc"

        logger.info(f"目标文件路径: {test_file}")

        # 检查桌面是否存在
        if not desktop_path.exists():
            logger.warning(f"⚠️  桌面目录不存在: {desktop_path}")
            logger.info("跳过此测试")
            pytest.skip("Desktop directory does not exist")
            return

        # 测试内容
        test_content = """这是一个测试文档

创建时间：{datetime}
用途：测试 VoxAgent 文件创建功能

内容：
- 第一行测试内容
- 第二行测试内容
- 第三行测试内容

测试成功！
""".format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 如果文件已存在，先删除（避免"文件已存在"错误）
        if test_file.exists():
            logger.info(f"文件已存在，先删除: {test_file}")
            test_file.unlink()

        # 使用工具创建文件
        tool = tool_registry.get_tool("file_create")
        result = tool._run(
            file_path=str(test_file),
            content=test_content
        )

        logger.info(f"工具返回结果: {result}")

        # 验证文件创建
        assert test_file.exists(), f"文件未创建: {test_file}"

        # 验证文件大小
        file_size = test_file.stat().st_size
        logger.info(f"文件大小: {file_size} bytes")
        assert file_size > 0, "文件为空"

        # 读取并验证内容
        with open(test_file, 'r', encoding='utf-8') as f:
            actual_content = f.read()

        assert actual_content == test_content, "文件内容不匹配"

        # ✅ 成功信息（文件不会被删除）
        logger.info("=" * 60)
        logger.info("✅ 测试通过: 在桌面创建 test.doc")
        logger.info(f"📄 文件位置: {test_file}")
        logger.info(f"📊 文件大小: {file_size} bytes")
        logger.info("⚠️  注意: 此文件不会被自动删除")
        logger.info("=" * 60)


def test_all():
    """运行所有测试"""
    logger.info("\n" + "=" * 70)
    logger.info("开始运行所有测试")
    logger.info("=" * 70)

    # 文件操作测试
    file_ops_test = TestFileOperations()
    file_ops_tests = [
        ("file_create", file_ops_test.test_file_create),
        ("file_read", file_ops_test.test_file_read),
        ("file_write", file_ops_test.test_file_write),
        ("file_append", file_ops_test.test_file_append),
        ("file_delete", file_ops_test.test_file_delete),
        ("file_search", file_ops_test.test_file_search),
        ("file_list", file_ops_test.test_file_list),
        ("file_find_recent", file_ops_test.test_file_find_recent),
        ("create_on_desktop", file_ops_test.test_create_file_on_desktop),  # ✨ 新增
    ]

    passed = 0
    failed = 0
    failed_tests = []

    # 运行文件操作测试
    logger.info("\n" + "=" * 70)
    logger.info("📁 文件操作测试")
    logger.info("=" * 70)

    for name, test_func in file_ops_tests:
        # ✨ 桌面测试不需要 setup/teardown
        if name != "create_on_desktop":
            file_ops_test.setup_method()

        try:
            test_func()
            passed += 1
            logger.info(f"✅ {name} - 通过")
        except Exception as e:
            failed += 1
            failed_tests.append(name)
            logger.error(f"❌ {name} - 失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # ✨ 桌面测试不需要清理
            if name != "create_on_desktop":
                file_ops_test.teardown_method()

    # 汇总结果
    logger.info("\n" + "=" * 70)
    logger.info("📊 测试汇总")
    logger.info("=" * 70)
    logger.info(f"总计: {passed + failed} 个测试")
    logger.info(f"✅ 通过: {passed}")
    logger.info(f"❌ 失败: {failed}")

    if failed_tests:
        logger.info("\n失败的测试:")
        for test in failed_tests:
            logger.info(f"   - {test}")

    logger.info("=" * 70)

    return passed, failed


if __name__ == "__main__":
    # 可以选择运行 pytest 或自定义测试
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        # 使用 pytest 运行
        pytest.main([__file__, "-v", "-s"])
    else:
        # 使用自定义测试运行器
        passed, failed = test_all()
        sys.exit(0 if failed == 0 else 1)
