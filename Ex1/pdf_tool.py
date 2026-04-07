"""
pdf_tool.py
Loads company_salaries.pdf, embeds it into a FAISS vector store,
and exposes a retrieval tool the agent can use to look up salary information.
"""

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.tools import Tool


def get_salary_tool(llm: ChatOpenAI) -> Tool:
    """
    Build and return a LangChain Tool for salary lookups from the PDF.

    Parameters
    ----------
    llm : ChatOpenAI
        The language model instance used by the RetrievalQA chain.

    Returns
    -------
    Tool
        A named tool the agent can invoke with a worker's name (or question)
        to retrieve salary information from the PDF.
    """
    pdf_path = os.getenv("PDF_PATH", "Resources/company_salaries.pdf")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    embeddings = OpenAIEmbeddings()
    index_dir = os.path.join(os.path.dirname(pdf_path), "faiss_index")

    if os.path.exists(index_dir):
        # Load the pre-built index from disk — no API calls needed
        vector_store = FAISS.load_local(
            index_dir, embeddings, allow_dangerous_deserialization=True
        )
        print(f"[pdf_tool] Loaded FAISS index from disk ({index_dir}).")
    else:
        # First run: embed the PDF and save the index for future runs
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)

        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(index_dir)
        print(f"[pdf_tool] Embedded PDF ({len(chunks)} chunks) and saved index to {index_dir}.")

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # Build RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
    )

    return Tool(
        name="SalaryLookup",
        func=qa_chain.invoke,
        description=(
            "Use this tool to find salary information for a worker. "
            "Input should be a question or a worker's full name, e.g. "
            "'What is the salary of Maya Levi?' or 'Dan Cohen salary'. "
            "Do NOT use this tool for questions about departments, cities, "
            "hierarchy, or any other worker details — use the SQL tools for those."
        ),
    )
