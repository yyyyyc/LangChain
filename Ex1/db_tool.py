"""
db_tool.py
Connects to the company_demo SQL Server database and returns a list of
LangChain tools the agent can use to query it.
"""

import re
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langchain.tools import Tool


def _strip_markdown(text: str) -> str:
    """Remove markdown code fences and stray quotes that the LLM wraps SQL/table names in."""
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    text = text.replace("`", "").strip()
    # Strip any leading/trailing quotes (paired or unpaired — the ReAct parser
    # sometimes strips the opening quote before we see the string, leaving only a trailing one)
    text = text.strip("\"'").strip()
    return text


def _wrap_tool(tool):
    """Return a new Tool that strips markdown from the input before calling the original."""
    def clean_func(query: str):
        return tool.run(_strip_markdown(query))

    return Tool(
        name=tool.name,
        func=clean_func,
        description=tool.description,
    )


def get_db_tools(llm: ChatOpenAI) -> list:
    """
    Create and return SQL database tools for the agent.

    Parameters
    ----------
    llm : ChatOpenAI
        The language model instance (needed by SQLDatabaseToolkit).

    Returns
    -------
    list
        A list of LangChain tools:
        - sql_db_list_tables
        - sql_db_schema
        - sql_db_query
        - sql_db_query_checker
    """
    connection_string = os.getenv("DB_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("DB_CONNECTION_STRING is not set in the .env file.")

    db = SQLDatabase.from_uri(
        connection_string,
        include_tables=["Workers", "Hierarchy", "Departments", "Cities"],
        sample_rows_in_table_info=3,
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    # Wrap tools that accept SQL/table input to strip markdown code fences
    SQL_INPUT_TOOLS = {"sql_db_query", "sql_db_query_checker", "sql_db_schema"}
    tools = [_wrap_tool(t) if t.name in SQL_INPUT_TOOLS else t for t in tools]

    print(f"[db_tool] Connected to database. Tables: {db.get_usable_table_names()}")
    return tools
