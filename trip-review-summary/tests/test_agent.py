# test_agent_like_executor.py
import asyncio
from uuid import uuid4

# Directly import your implemented Agent (no mocking required)
from agent import ReviewSummarizerAgent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()


async def test_agent_like_executor():
    """
    Mimic the calling pattern of ReviewSummarizerAgentExecutor.execute().
    Detached from the A2A framework dependencies for direct testing of agent.py.
    """
    print("🧪 启动 Agent 测试（模拟 Executor 调用方式）\n")

    # === 1. Initialize models (same as executor) ===
    query_chat_model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
    embedding_llm = OpenAIEmbeddings(model="text-embedding-3-large")

    # === 2. Create Agent instance (identical to executor) ===
    agent = ReviewSummarizerAgent(
        query_chat_model=query_chat_model, embedding_llm=embedding_llm
    )

    # === 3. Simulate user input (equivalent to RequestContext.get_user_input()) ===
    user_query = "总结上海迪士尼乐园关于排队时间的评价"
    context_id = str(uuid4())  # Simulate task.context_id

    print(f"👤 User input: {user_query}")
    print(f"🔖 Context ID: {context_id}\n")

    # === 4. Simulate the streaming execution flow from the executor ===
    try:
        async for chunk in agent.stream(user_query, context_id):
            content = chunk.get("content", "")
            is_complete = chunk.get("is_task_complete", False)
            require_input = chunk.get("require_user_input", False)

            if content:
                print(f"🤖 {content}")

            if is_complete:
                print("\n✅ Agent task completed successfully!")
                break

            if require_input:
                print("\n⚠️ Agent requests further user input, process paused.")
                break

    except Exception as e:
        print(f"\n❌ Error occurred during execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_agent_like_executor())
