import pytest
from langchain_openai import ChatOpenAI

from src.core.agent.agents.workers.windows_mail_agent import WinMailAgent
from src.core.agent.agents.workers.windows_music_agent import WinMusicAgent
from src.core.tools import tool_registry
from src.utils.config import config
from src.utils.langsmith_setup import setup_langsmith


@pytest.fixture
def mail_agent():
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "qwen3-next-80b-a3b-instruct"),
        temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
        max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
    )
    return WinMailAgent(tool_manager=tool_registry, llm=llm)

@pytest.fixture
def music_agent():
    qiniu_config = config.get("qiniu")
    llm = ChatOpenAI(
        api_key=qiniu_config.get("api_key"),
        base_url=qiniu_config.get("base_url"),
        model=qiniu_config.get("llm", {}).get("model", "qwen3-next-80b-a3b-instruct"),
        temperature=qiniu_config.get("llm", {}).get("temperature", 0.7),
        max_tokens=qiniu_config.get("llm", {}).get("max_tokens", 2000),
    )
    return WinMusicAgent(tool_manager=tool_registry, llm=llm)

def test_music_agent_run(music_agent):
    setup_langsmith()
    query = "我想听天天这首歌"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

    query = "停止播放"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

def test_music_agent_typo(music_agent):
    setup_langsmith()
    query = "我想听小真姑娘这首歌"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

    query = "停止播放"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

def test_music_agent_random(music_agent):
    setup_langsmith()
    query = "任意播放一首歌"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

    query = "停止播放"
    result = music_agent.invoke({
        "user_input": query
    })

    print("✅ MusicAgent returned:", result)

def test_mail_agent_run(mail_agent):
    setup_langsmith()
    query = "帮我查看有关CS5500的邮件"
    result = mail_agent.invoke({
        "user_input": query,
    })

    print("✅ MailAgent returned:", result)

    query = "帮我读一下Inbox里第一封邮件"
    result = mail_agent.invoke({
        "user_input": query,
    })
    print("✅ MailAgent returned:", result)