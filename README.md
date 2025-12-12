AI Workflow Engine — Coding Assignment
1. Overview

This project implements a minimal workflow/graph execution engine as required in the assignment PDF.
It supports:

Graph creation

Node execution

Conditional edges

State passing

Looping

A full example workflow (“Code Review Mini-Agent”)

FastAPI backend with 3 endpoints

JSON state logs

Polling run status

The engine works exactly as described in the assignment.

2. Project Structure

ai-agent-engine/
├─ app/
│  ├─ main.py                # FastAPI app + API endpoints
│  ├─ engine.py              # Core workflow engine
│  ├─ tools.py               # Tool registry + helper functions
│  ├─ store.py               # In-memory storage for graphs & runs
│  ├─ schemas.py             # Pydantic API schemas
│  └─ workflows/
│       └─ code_review.py    # Example workflow nodes
├─ graph_code_review.json    # Example graph definition
├─ requirements.txt
└─ README.md

3. Design Explanation
   
3.1 Nodes

Nodes are simple Python functions that:

Receive the shared workflow state

Modify the state

Return:

{"state": updated_state, "log": "message"}

Nodes are stored inside app/workflows/code_review.py.

3.2 Graph

A graph includes:

List of nodes

Edges (with optional conditions)

Entry node

Example in graph_code_review.json:

{
  "nodes": [
    {"name": "extract", "func": "extract"},
    {"name": "check_complexity", "func": "check_complexity"},
    {"name": "detect_issues", "func": "detect_issues"},
    {"name": "suggest", "func": "suggest_improvements"}
  ],
  "edges": {
    "extract": [{"to": "check_complexity"}],
    "check_complexity": [{"to": "detect_issues"}],
    "detect_issues": [
      {"when": "state.get('quality_score') < 0.9", "to": "suggest"},
      {"when": "state.get('quality_score') >= 0.9", "to": "suggest"}
    ],
    "suggest": [
      {"when": "state.get('quality_score') < 0.95", "to": "check_complexity"},
      {"when": "state.get('quality_score') >= 0.95", "to": ""}
    ]
  }
}

3.3 Engine Behavior

The engine:

Loads graph + state

Executes nodes in sequence

Evaluates conditions on edges

Updates state after each node

Supports loops by pointing back to previous nodes

Saves logs of every step

Stops when:

No next node

Max steps reached

Or explicit _loop_break

Implementation: app/engine.py.

3.4 API Endpoints

✔ Create graph

POST /graph/create

✔ Run workflow (background)

POST /graph/run

✔ Check state of a run

GET /graph/state/{run_id}

4. How to Run the Project

Step 1 — Install dependencies

pip install -r requirements.txt

Step 2 — Start FastAPI server

uvicorn app.main:app --reload --port 8000


Output:

Uvicorn running on http://127.0.0.1:8000

5. Creating a Graph

curl -X POST "http://127.0.0.1:8000/graph/create" \
-H "Content-Type: application/json" \
-d @graph_code_review.json


Output example:

{"graph_id": "bfffe085-4f30-46d5-9c35-fc24a2145f26"}

6. Running the Graph
   
curl -X POST "http://127.0.0.1:8000/graph/run" \
-H "Content-Type: application/json" \
-d '{
       "graph_id": "bfffe085-4f30-46d5-9c35-fc24a2145f26",
       "initial_state": {
           "code": "def foo(x): print(x); return x*2"
       }
     }'


Output:

{"run_id": "1d0d6ad4-813b-44ba-be41-867de8eae675"}

7. Checking Run Status
   
curl http://127.0.0.1:8000/graph/state/1d0d6ad4-813b-44ba-be41-867de8eae675

9. Sample Output (REAL OUTPUT from my run)

{
    "run_id":  "1d0d6ad4-813b-44ba-be41-867de8eae675",
    "state":  {
                  "code":  "def foo(x):\n    print(x)\n    return x*2\n\ndef bar(y):\n    return y+1",
                  "meta":  {
                               "extracted":  {
                                                 "functions":  [
                                                                   {
                                                                       "name":  "foo",
                                                                       "snippet":  "def foo(x): print(x) return x*2 def bar(y): return y+1"
                                                                   },
                                                                   {
                                                                       "name":  "bar",
                                                                       "snippet":  "return x*2 def bar(y): return y+1"
                                                                   }
                                                               ],
                                                 "function_count":  2
                                             },
                               "complexities":  [
                                                    {
                                                        "name":  "foo",
                                                        "complexity_score":  1,
                                                        "line_count":  1,
                                                        "max_indent":  0
                                                    },
                                                    {
                                                        "name":  "bar",
                                                        "complexity_score":  1,
                                                        "line_count":  1,
                                                        "max_indent":  0
                                                    }
                                                ],
                               "issues":  [
                                              {
                                                  "name":  "foo",
                                                  "issues":  [
                                                                 "debug print found"
                                                             ],
                                                  "issue_count":  1
                                              },
                                              {
                                                  "name":  "bar",
                                                  "issues":  [

                                                             ],
                                                  "issue_count":  0
                                              }
                                          ],
                               "suggestions":  [
                                                   {
                                                       "name":  "foo",
                                                       "suggestions":  [
                                                                           "Looks good; consider adding docstrings."
                                                                       ]
                                                   },
                                                   {
                                                       "name":  "bar",
                                                       "suggestions":  [
                                                                           "Looks good; consider adding docstrings."
                                                                       ]
                                                   }
                                               ]
                           },
                  "quality_score":  0.95
              },
    "status":  "completed",
    "log":  [
                {
                    "node":  "extract",
                    "log":  "extracted 2 functions",
                    "step":  1
                },
                {
                    "node":  "check_complexity",
                    "log":  "checked complexity, avg=1.00",
                    "step":  2
                },
                {
                    "node":  "detect_issues",
                    "log":  "detected 1 issues",
                    "step":  3
                },
                {
                    "node":  "suggest",
                    "log":  "suggested improvements",
                    "step":  4
                }
            ]
}
