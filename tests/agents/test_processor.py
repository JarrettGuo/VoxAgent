#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/26/25
@Author : guojarrett@gmail.com
@File   : test_processor.py
"""

from unittest.mock import Mock

import pytest

from src.core.models import ExecutionPlan, Task, TaskStatus
from src.core.processor import CommandProcessor


class TestCommandProcessor:
    """CommandProcessor 核心测试"""

    @pytest.fixture
    def mock_assistant(self):
        """创建 mock assistant"""
        assistant = Mock()
        assistant.config = Mock()
        assistant.config.get = Mock(return_value={})
        assistant.detector = Mock()
        assistant.is_processing = False
        return assistant

    @pytest.fixture
    def initialized_processor(self, mock_assistant):
        """创建已初始化的 processor"""
        processor = CommandProcessor(mock_assistant)
        processor._initialized = True
        processor.planner = Mock()
        processor.orchestrator = Mock()
        processor.summarizer = Mock()
        processor.tts_client = Mock()
        processor.audio_handler = Mock()

        # Mock conversation_manager 的 state 属性
        processor.conversation_manager = Mock()
        processor.conversation_manager.state = {
            "active": False,
            "retry_count": 0,
            "original_query": None,
            "messages": []
        }

        processor.error_handler = Mock()
        return processor

    # 1. 成功流程测试
    def test_handle_new_query_success(self, initialized_processor):
        """✅ 测试处理新查询成功"""
        text = "创建一个文件"

        # Mock 执行计划（包含任务）
        task = Task(
            task_id="task1",
            description="创建文件",
            assigned_agent="file",
            status=TaskStatus.PENDING
        )
        mock_plan = ExecutionPlan(
            plan_id="test_plan",
            tasks=[task],
            metadata={"feasibility": "feasible"}
        )
        initialized_processor.planner.plan_sync.return_value = mock_plan

        # Mock 执行结果
        mock_result = {
            "orchestrator_result": {
                "success": True,
                "total_steps": 1,
                "successful_steps": 1,
                "results": []
            }
        }
        initialized_processor.orchestrator.execute.return_value = mock_result
        initialized_processor.conversation_manager.needs_more_info.return_value = False
        initialized_processor.summarizer.summarize_sync.return_value = "任务完成"

        # 执行
        initialized_processor._handle_new_query(text)

        # 验证
        initialized_processor.planner.plan_sync.assert_called_once()
        initialized_processor.tts_client.speak.assert_called()

    # 2. 多轮对话测试
    def test_handle_new_query_needs_more_info(self, initialized_processor):
        """💬 测试需要补充信息（多轮对话）"""
        text = "查询天气"

        # 设置初始状态
        initialized_processor.conversation_manager.state["original_query"] = text

        task = Task(
            task_id="task1",
            description="查询天气",
            assigned_agent="search",
            status=TaskStatus.PENDING
        )
        mock_plan = ExecutionPlan(
            plan_id="test",
            tasks=[task],
            metadata={"feasibility": "feasible"}
        )
        initialized_processor.planner.plan_sync.return_value = mock_plan

        mock_result = {
            "orchestrator_result": {
                "success": False,
                "error_message": "未指定城市"
            }
        }
        initialized_processor.orchestrator.execute.return_value = mock_result
        initialized_processor.conversation_manager.needs_more_info.return_value = True

        # Mock error_handler 的两个方法
        from src.core.processor_modules import ErrorType
        initialized_processor.error_handler.analyze_error.return_value = (
            ErrorType.MISSING_INFO,
            {"message": "未指定城市"}
        )
        initialized_processor.error_handler.generate_clarification_question.return_value = "请问要查询哪个城市？"

        initialized_processor._handle_new_query(text)

        # 验证激活对话
        initialized_processor.conversation_manager.activate_conversation.assert_called_once()

    # 3. 计划执行异常测试
    def test_execute_plan_infeasible(self, initialized_processor):
        """❌ 测试不可行的计划"""
        plan = ExecutionPlan(
            plan_id="test",
            tasks=[],
            metadata={
                "feasibility": "infeasible",
                "reason": "超出系统能力"
            }
        )

        result = initialized_processor._execute_plan(plan)

        assert result["orchestrator_result"] is None
        assert "超出系统能力" in result["summary"]

    def test_execute_plan_orchestrator_exception(self, initialized_processor):
        """❌ 测试 Orchestrator 执行异常"""
        # 创建有效的 Task 对象
        task = Task(
            task_id="task1",
            description="测试任务",
            assigned_agent="file",
            status=TaskStatus.PENDING
        )

        plan = ExecutionPlan(
            plan_id="test",
            tasks=[task],
            metadata={"feasibility": "feasible"}
        )

        initialized_processor.orchestrator.execute.side_effect = Exception("Execution error")

        result = initialized_processor._execute_plan(plan)

        assert result["orchestrator_result"] is None
        assert "错误" in result["summary"]

    # 4. 错误处理测试
    def test_process_command_initialization_fails(self, mock_assistant):
        """❌ 测试系统初始化失败"""
        processor = CommandProcessor(mock_assistant)
        processor._initialized = False
        processor._initialize_system = Mock(return_value=False)
        processor.tts_client = Mock()

        processor.process_command()

        # 验证播放错误提示
        assert processor.tts_client.speak.called

    def test_process_command_exception_handling(self, initialized_processor):
        """❌ 测试异常捕获和处理"""
        initialized_processor.audio_handler.record_audio.side_effect = Exception("Recording error")

        initialized_processor.process_command()

        # 验证错误处理
        initialized_processor.tts_client.speak.assert_called()
        initialized_processor.conversation_manager.reset.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
