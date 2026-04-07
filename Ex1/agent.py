"""
agent.py
Assembles the LangChain ReAct agent by combining SQL tools and the
PDF salary tool under a single AgentExecutor with conversation memory.
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain import hub

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
  - Table names: Workers, Hierarchy, Departments, Cities (schema: dbo)
  - Join Workers to Departments on department_id
  - Join Workers to Cities on city_id
  - Hierarchy: worker_id reports to manager_id
  - Worker full name = first_name + ' ' + sur_name

IMPORTANT: When providing Action Input for any SQL tool, write the raw SQL or table
name only — no markdown, no backticks, no code fences. Just plain text.
"""


def build_agent() -> AgentExecutor:
    """
    Build and return the AgentExecutor with all tools and memory.

    Returns
    -------
    AgentExecutor
        The assembled agent ready to accept questions.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Gather tools from both sources
    sql_tools = get_db_tools(llm)
    salary_tool = get_salary_tool(llm)
    all_tools = sql_tools + [salary_tool]

    # Pull standard ReAct prompt from LangChain hub and append our context
    base_prompt = hub.pull("hwchase17/react-chat")

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
    )

    agent = create_react_agent(
        llm=llm,
        tools=all_tools,
        prompt=base_prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=all_tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=30,
    )

    return agent_executor
