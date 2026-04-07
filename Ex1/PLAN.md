# LangChain SQL + PDF Chatbot Agent — Implementation Plan

## Overview

A Python-based chatbot that uses a LangChain agent to answer natural-language questions
by querying two knowledge sources:

1. **SQL Server (`company_demo`)** — workers, hierarchy, departments, cities
2. **PDF (`company_salaries.pdf`)** — salary data per worker

---

## Database Schema (company_demo)

| Table | Key Columns |
|---|---|
| Departments | department_id (PK), name |
| Cities | city_id (PK, identity), city_name |
| Workers | worker_id (PK), sur_name, first_name, age, rank, department_id (FK), city_id (FK), gender, DOB |
| Hierarchy | relation_id (PK, identity), worker_id (FK, unique), manager_id (FK) |

**4 departments:** Human Resources, Finance, IT, Operations  
**8 cities:** Tel Aviv, Jerusalem, Haifa, Petah Tikva, Rishon LeZion, Netanya, Holon, Beersheba  
**30 workers** with a tree hierarchy: CEO → Directors → Managers → Staff

---

## File Structure

```
Ex1/
├── .env                  # LLM API key + DB connection string
├── requirements.txt      # Python dependencies
├── main.py               # Entry point / chat loop
├── db_tool.py            # SQL Server connection + LangChain SQL toolkit
├── pdf_tool.py           # PDF loader, vector store, retrieval tool
├── agent.py              # Agent assembly + executor
├── PLAN.md               # This file
└── Resources/
    ├── DB.sql
    ├── company_salaries.pdf
    └── Hierarchy.png
```

---

## Phase 1 — Project Setup

- Create `requirements.txt` with all dependencies
- Create `.env` template with placeholders for DB connection string and API key
- Verify folder structure is in place

**Dependencies:**
- `langchain`, `langchain-community`, `langchain-openai`
- `pyodbc`, `sqlalchemy` — SQL Server connectivity
- `pypdf` — PDF parsing
- `faiss-cpu` — local vector store for PDF embeddings
- `python-dotenv` — load `.env` variables

---

## Phase 2 — Database Tool (`db_tool.py`)

- Connect to `company_demo` via SQLAlchemy + pyodbc (ODBC Driver 17/18 for SQL Server)
- Use `langchain_community.utilities.SQLDatabase` to wrap the connection
- Use `langchain_community.agent_toolkits.SQLDatabaseToolkit` to auto-generate tools:
  - `sql_db_list_tables` — lists available tables
  - `sql_db_schema` — returns DDL for a table
  - `sql_db_query` — executes a SELECT query
  - `sql_db_query_checker` — validates SQL before running
- Expose the toolkit tools to the agent

---

## Phase 3 — PDF Salary Tool (`pdf_tool.py`)

- Load `Resources/company_salaries.pdf` with `PyPDFLoader`
- Split into chunks with `RecursiveCharacterTextSplitter`
- Embed chunks using `OpenAIEmbeddings` (or local alternative)
- Store in a local `FAISS` vector store
- Wrap with a `RetrievalQA` chain (LLM + retriever)
- Expose as a named `Tool` with description:
  > "Use this tool to find salary information for a specific worker. Input should be the worker's full name."

---

## Phase 4 — Agent Assembly (`agent.py`)

- Combine SQL toolkit tools + PDF salary tool into a single tool list
- Use `create_react_agent` with a system prompt that explains:
  - SQL tables contain worker details, hierarchy, departments, cities
  - The PDF tool contains salary data
  - Multi-step reasoning is required for compound questions
- Wrap with `AgentExecutor` (`verbose=True`, `handle_parsing_errors=True`)
- Add `ConversationBufferMemory` for multi-turn context

---

## Phase 5 — Chat Interface (`main.py`)

- Load environment variables from `.env`
- Initialize agent from `agent.py`
- Run a CLI loop: accept user input → pass to agent → print response
- Exit on `quit` / `exit`

---

## Example Query Flows

| Question | Reasoning Steps |
|---|---|
| "List workers in Finance" | SQL: JOIN Workers + Departments WHERE name = 'Finance' |
| "Salary of oldest worker under Maya Levi" | SQL: find Maya Levi's ID → get subordinates → find oldest → PDF: look up salary |
| "How many workers live in Tel Aviv?" | SQL: JOIN Workers + Cities WHERE city_name = 'Tel Aviv' |
| "Who is the highest-paid IT worker?" | SQL: get IT workers → PDF: look up each salary → compare |
| "Who reports to Dan Cohen?" | SQL: Hierarchy WHERE manager_id = Dan Cohen's worker_id |
