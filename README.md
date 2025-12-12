# AI Agent Engine – Coding Assignment

This project implements a minimal agentic workflow engine using FastAPI.  
It supports creation of directed graphs, conditional edges, execution of nodes,  
state mutation, logging, and workflow execution with polling.

## 🚀 How to Run

### 1. Create Virtual Environment
python -m virtualenv .venv
.venv\Scripts\activate

### 2. Install Requirements
pip install -r requirements.txt

### 3. Start API Server
uvicorn app.main:app --reload --port 8000

Server runs at:
http://127.0.0.1:8000

Swagger docs:
http://127.0.0.1:8000/docs

---

## 🧠 Code Review Workflow

A sample workflow graph is defined in `graph_code_review.json`.

To create this graph:

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/graph/create"
-Body (Get-Content -Raw graph_code_review.json) `
-ContentType 'application/json'


To start a run:

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/graph/run"
-Body '{"graph_id":"<your_graph_id>","initial_state":{"code":"...your code..."}}' `
-ContentType 'application/json'


To poll:

GET /graph/state/<run_id>

## 📄 Files Included

app/
main.py
engine.py
schemas.py
tools.py
store.py
workflows/
code_review.py
requirements.txt
graph_code_review.json
README.md

## ✔️ Output Example

The engine produces:

- extracted functions
- complexity metrics
- issues
- suggestions
- quality score
- execution log

Status = completed

