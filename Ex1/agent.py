"""
agent.py
Assembles the LangChain ReAct agent by combining SQL tools and the
PDF salary tool under a single AgentExecutor with conversation memory.
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import PromptTemplate

from db_tool import get_db_tools
from pdf_tool import get_salary_tool


SYSTEM_PROMPT_SUFFIX = """
You are a helpful HR assistant for a company. You have access to two types of information:

1. **Company Database (SQL tools)** — use these to answer questions about:
   - Workers: names, age, gender, date of birth, rank/title, department, city
   - Departments: Human Resources, Finance, IT, Operations
   - Cities: where workers live
   - Hierarchy: who reports to whom (manager-subordinate relationships)

2. **SalaryLookup tool (PDF)** — use this ONLY to find salary figures for specific workers.

When a question requires both (e.g. "salary of the oldest worker under Maya Levi"):
  Step 1: Use SQL tools to find the relevant worker(s).
  Step 2: Use SalaryLookup to get their salary.

Always think step by step. When writing SQL queries:
  - The database is **Microsoft SQL Server** — use T-SQL syntax only.
  - Use TOP N (e.g. SELECT TOP 1 ...), never LIMIT.
  - Use GETDATE() for the current date/time, not NOW().
  - Table names: Workers, Hierarchy, Departments, Cities (schema: dbo)
  - Join Workers to Departments on department_id
  - Join Workers to Cities on city_id
  - Hierarchy: worker_id reports to manager_id
  - Worker full name = first_name + ' ' + sur_name

IMPORTANT: When providing Action Input for any SQL tool, write the raw SQL or table
name only — no markdown, no backticks, no code fences. Just plain text.
"""


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
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Gather tools from both sources
    sql_tools = get_db_tools(llm)
    salary_tool = get_salary_tool(llm)
    all_tools = sql_tools + [salary_tool]

    # Local ReAct-chat prompt (equivalent to hwchase17/react-chat)
    base_prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT_SUFFIX + """\n
Assistant can ask the user to use tools to look up information that may be helpful in answering the users original question. The tools the human can use are:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""
    )

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
