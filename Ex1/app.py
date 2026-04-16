"""
app.py
Flask web interface for the Company HR Chatbot.
Run:  python app.py
"""

import io
import json
import os
import queue
import sys
import shutil
import threading

from flask import Flask, Response, request, jsonify, render_template, stream_with_context
from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler

load_dotenv()
os.environ.setdefault("LANGSMITH_TRACING", "false")  # silence warning when key is absent

app = Flask(__name__)
_agent_executor = None


# ── SSE callback handler ────────────────────────────────────────────────────

class _SSEHandler(BaseCallbackHandler):
    """Pushes LangChain agent events into a queue as SSE-ready dicts."""

    def __init__(self, q: queue.Queue):
        self._q = q

    # LLM token streaming (fires when streaming=True on the LLM)
    def on_llm_new_token(self, token: str, **kwargs):
        if token:
            self._q.put({"type": "token", "data": token})

    # Agent decides to call a tool
    def on_agent_action(self, action, **kwargs):
        self._q.put({
            "type": "action",
            "tool": action.tool,
            "input": str(action.tool_input),
        })

    # Tool finished successfully
    def on_tool_end(self, output: str, **kwargs):
        self._q.put({"type": "observation", "data": str(output)})

    # Tool raised an exception
    def on_tool_error(self, error, **kwargs):
        self._q.put({"type": "observation", "data": f"Error: {error}", "is_error": True})


# ── Agent singleton ─────────────────────────────────────────────────────────

def get_agent():
    global _agent_executor
    if _agent_executor is None:
        from agent import build_agent
        _agent_executor = build_agent()
    return _agent_executor


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "No question provided."}), 400

    if not os.getenv("OPENAI_API_KEY"):
        return jsonify({"error": "OPENAI_API_KEY is not set in .env"}), 500

    q: queue.Queue = queue.Queue()
    handler = _SSEHandler(q)
    executor = get_agent()

    def run_agent():
        try:
            result = executor.invoke({"input": question}, callbacks=[handler])
            messages = executor.memory_messages
            memory_log = [
                {"role": "human" if m.type == "human" else "ai", "content": m.content}
                for m in messages
            ]
            q.put({"type": "answer", "data": result.get("output", ""), "memory": memory_log})
        except Exception as e:
            q.put({"type": "error", "data": str(e)})
        finally:
            q.put(None)  # sentinel → close stream

    threading.Thread(target=run_agent, daemon=True).start()

    def generate():
        while True:
            item = q.get()
            if item is None:
                yield "data: [DONE]\n\n"
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/delete-embeddings", methods=["POST"])
def delete_embeddings():
    global _agent_executor
    pdf_path = os.getenv("PDF_PATH", "Resources/company_salaries.pdf")
    index_dir = os.path.join(os.path.dirname(pdf_path), "faiss_index")

    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
        _agent_executor = None  # Force rebuild + re-embed on next request
        return jsonify({
            "success": True,
            "message": "Embeddings deleted. Agent will reinitialize on next query.",
        })
    return jsonify({"success": False, "message": "No embeddings found."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
