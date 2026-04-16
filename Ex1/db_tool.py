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
    """Remove markdown code fences and wrapping quotes that the LLM adds around SQL/table names."""
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
    text = text.replace("`", "").strip()

    # Case 1: matched pair of surrounding quotes — strip both.
    # e.g. "SELECT ..." or 'Workers'
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    # Case 2: the ReAct parser already stripped the opening quote before we see the
    # string, leaving only a stray trailing double-quote (e.g. "SELECT ... Levi'").
    # Strip it. We only do this for " (not '), because a query can legitimately end
    # with a single-quote string literal like WHERE name = 'Smith'.
    elif text.endswith('"'):
        text = text[:-1].strip()

    # Trailing semicolons are not needed for single-statement pyodbc execution and
    # interact badly with stray quotes — remove them.
    text = text.rstrip(';').strip()

    return text


def _to_sql_server(sql: str) -> str:
    """
    Rewrite common MySQL/PostgreSQL constructs to SQL Server T-SQL so that
    the agent's queries work even when the LLM emits non-SQL-Server syntax.

    Transformations applied:
      LIMIT n               → TOP n  (injected after SELECT / SELECT DISTINCT)
      LIMIT n OFFSET m      → OFFSET m ROWS FETCH NEXT n ROWS ONLY
      ILIKE 'x'             → LIKE 'x'  (SQL Server LIKE is already case-insensitive)
    """
    sql = sql.strip()

    # LIMIT n OFFSET m  →  OFFSET m ROWS FETCH NEXT n ROWS ONLY
    # Must be checked before the plain LIMIT case.
    limit_offset = re.search(
        r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\s*$', sql, re.IGNORECASE
    )
    if limit_offset:
        n, m = limit_offset.group(1), limit_offset.group(2)
        sql = sql[:limit_offset.start()].rstrip()
        sql = f"{sql} OFFSET {m} ROWS FETCH NEXT {n} ROWS ONLY"
    else:
        # Plain LIMIT n  →  TOP n  (inject after SELECT or SELECT DISTINCT)
        limit_simple = re.search(r'\bLIMIT\s+(\d+)\s*$', sql, re.IGNORECASE)
        if limit_simple:
            n = limit_simple.group(1)
            sql = sql[:limit_simple.start()].rstrip()
            sql = re.sub(
                r'\bSELECT(\s+DISTINCT\b)?',
                lambda m: f"SELECT{m.group(1) or ''} TOP {n}",
                sql, count=1, flags=re.IGNORECASE,
            )

    # ILIKE → LIKE  (SQL Server LIKE is case-insensitive by default)
    sql = re.sub(r'\bILIKE\b', 'LIKE', sql, flags=re.IGNORECASE)

    return sql


def _wrap_tool(tool):
    """Return a new Tool that strips markdown and normalises SQL Server syntax before calling the original."""
    def clean_func(query: str):
        query = _strip_markdown(query)
        query = _to_sql_server(query)
        return tool.run(query)

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
