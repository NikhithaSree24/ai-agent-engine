from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from app.schemas import GraphCreateRequest, GraphCreateResponse, RunRequest, RunResponse, RunStateResponse
from app.store import store
from app import workflows
from app import engine as engine_module
import uuid
from typing import Dict, Any
from importlib import import_module

app = FastAPI(title="Minimal Workflow Engine")

# Helper to build graph object with callable node functions referenced
def build_graph(req: GraphCreateRequest) -> Dict[str, Any]:
    nodes = {}
    for n in req.nodes:
        # `n.func` is the registered name; we will look up in known workflow registries OR default to workflows module
        # First check nodes in workflows.code_review.NODE_REGISTRY etc
        callable_fn = None
        # look into all workflow modules that expose NODE_REGISTRY
        # current simple approach: check workflows package modules for the function name
        # fallback: if func equals node name in code_review.NODE_REGISTRY, use it
        # We'll support 'module:func' syntax as well e.g. "code_review:extract"
        func_spec = n.func
        if ":" in func_spec:
            module_name, func_name = func_spec.split(":", 1)
            mod = import_module(f"app.workflows.{module_name}")
            callable_fn = mod.NODE_REGISTRY.get(func_name)
        else:
            # search in known workflow modules
            for mod_name in ["code_review"]:
                mod = import_module(f"app.workflows.{mod_name}")
                if func_spec in mod.NODE_REGISTRY:
                    callable_fn = mod.NODE_REGISTRY[func_spec]
                    break
        if callable_fn is None:
            raise Exception(f"Unknown node function '{func_spec}'")
        nodes[n.name] = {"func_name": n.func, "config": n.config, "callable": callable_fn}
    # normalize edges
    edges = {}
    for k,v in req.edges.items():
        if isinstance(v, str):
            edges[k] = v
        else:
            # v might be EdgeWhen or list
            items = []
            if not isinstance(v, list):
                v = [v]
            for vv in v:
                # vv is pydantic model -> dict
                items.append({"to": vv.to, "when": getattr(vv, "when", None)})
            edges[k] = items
    # pick entry as first node in list
    entry = req.nodes[0].name if req.nodes else None
    graph_id = str(uuid.uuid4())
    return {"graph_id": graph_id, "nodes": nodes, "edges": edges, "entry": entry}

@app.post("/graph/create", response_model=GraphCreateResponse)
def create_graph(req: GraphCreateRequest):
    try:
        graph = build_graph(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    store.save_graph(graph["graph_id"], graph)
    return {"graph_id": graph["graph_id"]}

@app.post("/graph/run", response_model=RunResponse)
async def run_graph_endpoint(req: RunRequest, background_tasks: BackgroundTasks):
    graph = store.get_graph(req.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="graph not found")
    run_id = str(uuid.uuid4())
    # initialize run object
    store.save_run(run_id, {"run_id": run_id, "state": req.initial_state or {}, "status": "queued", "log": [], "graph_id": req.graph_id})
    # run in background
    background_tasks.add_task(engine_module.run_graph, graph, req.initial_state or {}, run_id)
    return {"run_id": run_id}

@app.get("/graph/state/{run_id}", response_model=RunStateResponse)
def get_run_state(run_id: str):
    r = store.get_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run_id": run_id, "state": r.get("state", {}), "status": r.get("status","unknown"), "log": r.get("log", [])}

# Minimal WebSocket to stream logs (optional). Client connects and polls run.
@app.websocket("/ws/run/{run_id}")
async def websocket_run(ws: WebSocket, run_id: str):
    await ws.accept()
    try:
        while True:
            r = store.get_run(run_id)
            if not r:
                await ws.send_json({"error": "run not found"})
                await ws.close()
                return
            await ws.send_json({"state": r.get("state", {}), "status": r.get("status", "unknown"), "log": r.get("log", [])})
            if r.get("status") != "running" and r.get("status") != "queued":
                await ws.close()
                return
            await asyncio.sleep(1.0)
    except Exception:
        await ws.close()
