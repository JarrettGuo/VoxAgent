from src.utils.logger import logger
from typing import Dict, Any
from abc import ABC, abstractmethod
import time

class BaseAgent(ABC):
    """基础Agent接口"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, task_description: str) -> Dict[str, Any]:
        """
        执行任务

        参数:
            task_description: 任务描述

        返回:
            执行结果字典
        """
        pass


# ============================================================================
# Mock Agents
# ============================================================================

class MockCodeAgent(BaseAgent):
    """模拟代码执行Agent"""

    def __init__(self):
        super().__init__("CodeAgent")
        self.execution_count = 0

    def execute(self, task_description: str) -> Dict[str, Any]:
        """执行代码任务"""
        logger.info(f"[{self.name}] Executing: {task_description}")
        self.execution_count += 1

        # 模拟执行时间
        time.sleep(0.1)

        # 模拟不同的代码执行场景
        if "error" in task_description.lower():
            raise Exception("Code execution failed: Syntax error")

        if "calculate" in task_description.lower():
            return {
                "output": "Calculation result: 42",
                "execution_time": 0.1,
                "success": True
            }

        if "file" in task_description.lower():
            return {
                "output": "File created successfully",
                "file_path": "/tmp/output.txt",
                "success": True
            }

        return {
            "output": f"Code executed: {task_description}",
            "success": True
        }


class MockSearchAgent(BaseAgent):
    """模拟搜索Agent"""

    def __init__(self):
        super().__init__("SearchAgent")
        self.search_count = 0

    def execute(self, task_description: str) -> Dict[str, Any]:
        """执行搜索任务"""
        logger.info(f"[{self.name}] Searching: {task_description}")
        self.search_count += 1

        time.sleep(0.1)

        # 模拟搜索结果
        keywords = task_description.lower()

        if "weather" in keywords:
            return {
                "results": [
                    {"title": "Weather Today", "snippet": "Sunny, 25°C"},
                    {"title": "Weather Forecast", "snippet": "Clear skies expected"}
                ],
                "result_count": 2,
                "success": True
            }

        if "news" in keywords:
            return {
                "results": [
                    {"title": "Latest News", "snippet": "Breaking news story"},
                    {"title": "Tech News", "snippet": "New AI breakthrough"}
                ],
                "result_count": 2,
                "success": True
            }

        return {
            "results": [{"title": "Search Result", "snippet": f"Found: {task_description}"}],
            "result_count": 1,
            "success": True
        }


class MockFileAgent(BaseAgent):
    """模拟文件操作Agent"""

    def __init__(self):
        super().__init__("FileAgent")
        self.operation_count = 0
        self.files = {}  # 模拟文件系统

    def execute(self, task_description: str) -> Dict[str, Any]:
        """执行文件操作"""
        logger.info(f"[{self.name}] File operation: {task_description}")
        self.operation_count += 1

        time.sleep(0.1)

        keywords = task_description.lower()

        if "create" in keywords or "write" in keywords:
            filename = "test_file.txt"
            self.files[filename] = "Mock file content"
            return {
                "operation": "create",
                "filename": filename,
                "size": 100,
                "success": True
            }

        if "read" in keywords:
            return {
                "operation": "read",
                "content": "Mock file content from disk",
                "success": True
            }

        if "delete" in keywords:
            return {
                "operation": "delete",
                "files_deleted": 1,
                "success": True
            }

        return {
            "operation": "unknown",
            "message": f"File operation: {task_description}",
            "success": True
        }


class MockDatabaseAgent(BaseAgent):
    """模拟数据库Agent"""

    def __init__(self):
        super().__init__("DatabaseAgent")
        self.query_count = 0

    def execute(self, task_description: str) -> Dict[str, Any]:
        """执行数据库操作"""
        logger.info(f"[{self.name}] Database query: {task_description}")
        self.query_count += 1

        time.sleep(0.1)

        keywords = task_description.lower()

        if "select" in keywords or "query" in keywords:
            return {
                "operation": "SELECT",
                "rows_returned": 10,
                "data": [{"id": i, "name": f"Record {i}"} for i in range(3)],
                "success": True
            }

        if "insert" in keywords:
            return {
                "operation": "INSERT",
                "rows_affected": 1,
                "success": True
            }

        if "update" in keywords:
            return {
                "operation": "UPDATE",
                "rows_affected": 5,
                "success": True
            }

        return {
            "operation": "UNKNOWN",
            "message": f"Database operation: {task_description}",
            "success": True
        }

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEMONSTRATING MOCK AGENTS")
    print("=" * 60)

    print("\n📝 Testing CodeAgent:")
    code_agent = MockCodeAgent()
    result = code_agent.execute("Calculate factorial of 10")
    print(f"Result: {result}")

    print("\n🔍 Testing SearchAgent:")
    search_agent = MockSearchAgent()
    result = search_agent.execute("Search for weather forecast")
    print(f"Result: {result}")

    print("\n📁 Testing FileAgent:")
    file_agent = MockFileAgent()
    result = file_agent.execute("Create a new file")
    print(f"Result: {result}")

    print("\n🗄️ Testing DatabaseAgent:")
    db_agent = MockDatabaseAgent()
    result = db_agent.execute("Select all users from database")
    print(f"Result: {result}")