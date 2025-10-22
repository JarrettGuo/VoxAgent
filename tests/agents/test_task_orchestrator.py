import sys
from src.utils.langsmith_setup import setup_langsmith

from src.utils.logger import logger
from src.utils.config import config

def main():
    """主测试运行函数"""

    setup_langsmith()

    logger.info("=" + "=" * 70)
    logger.info(" " * 15 + "TASK ORCHESTRATOR TEST SUITE")
    logger.info("=" * 70)

    try:
        # Import the orchestrator
        from src.core.agent.agents.task_orchestrator import TaskOrchestrator
        logger.info("✓ TaskOrchestrator imported successfully")

        from src.core.agent.entities.agent_entity import AgentConfig
        from langchain_openai import ChatOpenAI

        # ✅ 从配置文件中读取七牛云配置
        qiniu_config = config.get("qiniu")
        if not qiniu_config:
            raise ValueError("❌ 未找到七牛云配置,请检查 config/config.yaml")

        # ✅ 使用七牛云配置创建 LLM
        llm = ChatOpenAI(
            api_key=qiniu_config.get("api_key"),
            base_url=qiniu_config.get("base_url"),
            model=qiniu_config.get("llm", {}).get("model", "gpt-4o-mini"),
            temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
            max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
        )

        agent_config = AgentConfig(max_iterations=5)
        # Import mock agents
        from mock_agents.mocks import (
            MockCodeAgent,
            MockSearchAgent,
            MockFileAgent,
            MockDatabaseAgent
        )
        logger.info("✓ Mock agents imported successfully")

        logger.info("=" + "-" * 70)
        logger.info("Running comprehensive tests...")
        logger.info("-" * 70)

        # Test 1: Simple execution
        logger.info("=" + "=" * 70)
        logger.info("TEST 1: Simple Single-Step Execution")
        logger.info("=" * 70)

        agents = {
            "code": MockCodeAgent(),
            "search": MockSearchAgent(),
        }

        orchestrator = TaskOrchestrator(agents)
        logger.info("Task Orchestrator Initialized")

        plan = {
            "steps": [
                {
                    "description": "Calculate the sum of 1 to 100",
                    "agent": "code"
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"=📊 Results:")
        logger.info(f"  ✓ Success: {result['success']}")
        logger.info(f"  ✓ Total Steps: {result['total_steps']}")
        logger.info(f"  ✓ Successful Steps: {result['successful_steps']}")
        logger.info(f"  ✓ Message: {result['message']}")

        assert result['success'] == True
        assert result['successful_steps'] == 1
        logger.info("=✅ TEST 1 PASSED!")

        # Test 2: Multi-step execution
        logger.info("=" + "=" * 70)
        logger.info("TEST 2: Multi-Step Execution with Different Agents")
        logger.info("=" * 70)

        agents = {
            "code": MockCodeAgent(),
            "search": MockSearchAgent(),
            "file": MockFileAgent(),
        }

        orchestrator = TaskOrchestrator(agents)

        plan = {
            "steps": [
                {
                    "description": "Search for weather information",
                    "agent": "search"
                },
                {
                    "description": "Calculate average temperature",
                    "agent": "code"
                },
                {
                    "description": "Write results to file",
                    "agent": "file"
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"=📊 Results:")
        logger.info(f"  ✓ Success: {result['success']}")
        logger.info(f"  ✓ Total Steps: {result['total_steps']}")
        logger.info(f"  ✓ Successful Steps: {result['successful_steps']}")
        logger.info(f"  ✓ Message: {result['message']}")

        logger.info(f"=📋 Step Details:")
        for i, step_result in enumerate(result['results'], 1):
            logger.info(f"  Step {i}: {step_result['description']}")
            logger.info(f"    → Status: {step_result['status']}")
            if 'result' in step_result:
                logger.info(f"    → Output: {list(step_result['result'].keys())}")

        assert result['success'] == True
        assert result['successful_steps'] == 3
        logger.info("=✅ TEST 2 PASSED!")

        # Test 3: Error handling
        logger.info("=" + "=" * 70)
        logger.info("TEST 3: Error Handling")
        logger.info("=" * 70)

        agents = {
            "code": MockCodeAgent(),
            "search": MockSearchAgent(),
        }

        orchestrator = TaskOrchestrator(agents)

        plan = {
            "steps": [
                {
                    "description": "Search for information",
                    "agent": "search"
                },
                {
                    "description": "Execute code with error",
                    "agent": "code"
                },
                {
                    "description": "This step should not execute",
                    "agent": "search"
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"=📊 Results:")
        logger.info(f"  ✓ Success: {result['success']}")
        logger.info(f"  ✓ Successful Steps: {result['successful_steps']}")
        logger.info(f"  ✓ Failed Steps: {result['failed_steps']}")
        logger.info(f"  ✓ Error: {result['error_message']}")
        logger.info(f"  ✓ Message: {result['message']}")

        assert result['success'] == False
        assert result['successful_steps'] == 1
        assert result['failed_steps'] == 1
        logger.info("=✅ TEST 3 PASSED!")

        # Test 4: Complex workflow
        logger.info("=" + "=" * 70)
        logger.info("TEST 4: Complex Multi-Agent Workflow")
        logger.info("=" * 70)

        agents = {
            "code": MockCodeAgent(),
            "search": MockSearchAgent(),
            "file": MockFileAgent(),
            "database": MockDatabaseAgent(),
        }

        orchestrator = TaskOrchestrator(agents)

        plan = {
            "steps": [
                {
                    "description": "Query database for user data",
                    "agent": "database"
                },
                {
                    "description": "Search for news articles",
                    "agent": "search"
                },
                {
                    "description": "Calculate statistics from data",
                    "agent": "code"
                },
                {
                    "description": "Create report file",
                    "agent": "file"
                },
                {
                    "description": "Update database with results",
                    "agent": "database"
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"=📊 Results:")
        logger.info(f"  ✓ Success: {result['success']}")
        logger.info(f"  ✓ Total Steps: {result['total_steps']}")
        logger.info(f"  ✓ Successful Steps: {result['successful_steps']}")
        logger.info(f"  ✓ Message: {result['message']}")

        logger.info(f"=📋 Detailed Execution Flow:")
        for i, step_result in enumerate(result['results'], 1):
            logger.info(f"  Step {i}: {step_result['description'][:50]}...")
            logger.info(f"    → Status: {step_result['status']}")
            if 'result' in step_result and step_result['result']:
                result_preview = str(step_result['result'])[:80]
                logger.info(f"    → Result: {result_preview}...")

        # Verify agent usage
        logger.info(f"=📈 Agent Usage Statistics:")
        logger.info(f"  → CodeAgent: {agents['code'].execution_count} executions")
        logger.info(f"  → SearchAgent: {agents['search'].search_count} searches")
        logger.info(f"  → FileAgent: {agents['file'].operation_count} operations")
        logger.info(f"  → DatabaseAgent: {agents['database'].query_count} queries")

        assert result['success'] == True
        assert result['successful_steps'] == 5
        logger.info("=✅ TEST 4 PASSED!")

        # Test 5: Unknown agent
        logger.info("=" + "=" * 70)
        logger.info("TEST 5: Handling Unknown Agent Type")
        logger.info("=" * 70)

        agents = {
            "code": MockCodeAgent(),
        }

        orchestrator = TaskOrchestrator(agents)

        plan = {
            "steps": [
                {
                    "description": "Execute with known agent",
                    "agent": "code"
                },
                {
                    "description": "Execute with unknown agent",
                    "agent": "unknown_agent_type"
                }
            ]
        }

        result = orchestrator.execute(plan)

        logger.info(f"📊 Results:")
        logger.info(f"  ✓ Success: {result['success']}")
        logger.info(f"  ✓ Successful Steps: {result['successful_steps']}")
        logger.info(f"  ✓ Failed Steps: {result['failed_steps']}")
        logger.info(f"  ✓ Error: {result['error_message']}")

        assert result['success'] == False
        assert "Unknown agent type" in result['error_message']
        logger.info("=✅ TEST 5 PASSED!")

        # Summary
        logger.info("=" + "=" * 70)
        logger.info(" " * 20 + "🎉 ALL TESTS PASSED! 🎉")
        logger.info("=" * 70)
        logger.info("=✓ The TaskOrchestrator is working correctly!")
        logger.info("✓ All mock agents are functioning as expected!")
        logger.info("✓ Error handling is robust!")
        logger.info("✓ Multi-agent workflows execute successfully!")

        logger.info("=" + "=" * 70)
        logger.info("Next Steps:")
        logger.info("  1. Replace mock agents with your real agent implementations")
        logger.info("  2. Integrate the orchestrator into your _execute_plan method")
        logger.info("  3. Add more sophisticated error recovery strategies")
        logger.info("  4. Consider adding parallel execution for independent steps")
        logger.info("=" * 70 + "=")

        return 0

    except ImportError as e:
        logger.info(f"=❌ Import Error: {e}")
        logger.info("\nMake sure you have:")
        logger.info("  1. execution_orchestrator.py in the same directory")
        logger.info("  2. mock_agents.py with all the agent classes")
        logger.info("  3. langgraph installed: pip install langgraph")
        return 1

    except AssertionError as e:
        logger.info(f"=❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except Exception as e:
        logger.info(f"=❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())