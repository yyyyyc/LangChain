# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repo contains **Ex1** — a LangChain ReAct agent that answers natural-language HR questions by combining two data sources:
- A **SQL Server database** (`company_demo`) with worker, hierarchy, department, and city data
- A **PDF** (`company_salaries.pdf`) embedded in a FAISS vector store for salary lookups

## Running the Chatbot

```bash
cd Ex1
python main.py
```

Requires `.env` to be populated (copy from `.env.example`):
```
OPENAI_API_KEY=...
DB_CONNECTION_STRING=mssql+pyodbc://USER:PWD@HOST\INSTANCE/DB_NAME?driver=ODBC+Driver+17+for+SQL+Server
PDF_PATH=Resources/company_salaries.pdf
```

## Installing Dependencies

```bash
cd Ex1
pip install -r requirements.txt
```

Requires **ODBC Driver 17 or 18 for SQL Server** installed on the system.

## Architecture

```
main.py       → CLI chat loop; loads .env, calls build_agent(), invokes agent per turn
agent.py      → Assembles AgentExecutor: LLM (gpt-4o) + SQL tools + SalaryLookup + memory
db_tool.py    → Connects to SQL Server via SQLAlchemy/pyodbc; wraps SQLDatabaseToolkit tools
pdf_tool.py   → Loads/embeds PDF with FAISS; exposes SalaryLookup Tool via RetrievalQA
```

### Key design details

- **SQL tools** are wrapped in `_wrap_tool()` to strip markdown code fences the LLM sometimes emits before executing queries.
- **FAISS index** is cached to `Resources/faiss_index/` on first run; subsequent runs load from disk without re-embedding.
- The agent uses `hwchase17/react-chat` from LangChain Hub with a custom suffix that explains the SQL schema and when to use the PDF tool.
- `ConversationBufferMemory` (key: `chat_history`) provides multi-turn context.
- `max_iterations=30` to handle compound queries that require multiple tool calls.

### Database schema (SQL Server, schema: `dbo`)

| Table | Key columns |
|---|---|
| Workers | worker_id, first_name, sur_name, age, rank, department_id, city_id, gender, DOB |
| Departments | department_id, name |
| Cities | city_id, city_name |
| Hierarchy | relation_id, worker_id (unique), manager_id |

Worker full name in queries: `first_name + ' ' + sur_name`
