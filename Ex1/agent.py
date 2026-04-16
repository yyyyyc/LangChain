"""
agent.py
Assembles the LangChain ReAct agent by combining SQL tools and the
PDF salary tool under a single AgentExecutor with conversation memory.
"""

import os

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub

from db_tool import get_db_tools
from pdf_tool import get_salary_tool


def _build_llm_and_embeddings():
    """
    Create the LLM and embeddings objects based on the LLM_PROVIDER env var.

    Supported providers:
      - "openai"  (default) — uses OPENAI_API_KEY
      - "azure"              — uses AZURE_OPENAI_* variables
    """
    import httpx
    http_client = httpx.Client(verify=False)
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "azure":
        from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            temperature=0,
            http_client=http_client,
        )
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            http_client=http_client,
        )
        print(f"[agent] Using Azure OpenAI (endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')})")
    else:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            http_client=http_client,
        )
        embeddings = OpenAIEmbeddings(http_client=http_client)
        print("[agent] Using OpenAI")

    return llm, embeddings


class AgentWrapper:
    """
    Thin wrapper around RunnableWithMessageHistory that keeps a
    compatible .invoke() interface and exposes conversation messages.
    """

    def __init__(self, runnable: RunnableWithMessageHistory, get_history):
        self._runnable = runnable
        self._get_history = get_history

    def invoke(self, inputs: dict, callbacks: list | None = None) -> dict:
        config: dict = {"configurable": {"session_id": "default"}}
        if callbacks:
            config["callbacks"] = callbacks
        return self._runnable.invoke(inputs, config=config)

    @property
    def memory_messages(self) -> list:
        return self._get_history("default").messages


def build_agent() -> AgentWrapper:
    """
    Build and return an AgentWrapper with all tools and per-session memory.

    Returns
    -------
    AgentWrapper
        The assembled agent ready to accept questions.
    """
    llm, embeddings = _build_llm_and_embeddings()

    # Gather tools from both sources
    sql_tools = get_db_tools(llm)
    salary_tool = get_salary_tool(llm, embeddings)
    all_tools = sql_tools + [salary_tool]

    # Pull standard ReAct prompt from LangChain hub
    base_prompt = hub.pull("hwchase17/react-chat")

    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=base_prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=30,
    )

    # Per-call session store — each build_agent() call starts fresh
    session_store: dict[str, InMemoryChatMessageHistory] = {}

    def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in session_store:
            session_store[session_id] = InMemoryChatMessageHistory()
        return session_store[session_id]

    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return AgentWrapper(agent_with_history, get_session_history)
