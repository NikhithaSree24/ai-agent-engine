# Core engine that executes nodes based on edges, supports branching and looping.
import asyncio
import uuid
from typing import Dict, Any, Callable, List, Optional
from app.store import store
import ast

# Safety note: for simple conditional expressions we will eval Python expressions
# with restricted globals. This is for exercise/demo only — in production use a proper safe evaluator.
def eval_condition(cond: str, state: Dict[str, Any]) -> bool:
    if not cond:
        return True
    try:
        # Only expose `state` as the variable
        return bool(eval(cond, {"__builtins__": {}}, {"state": state}))
    except Exception:
        return False

async def run_graph(graph: Dict[str, Any], initial_state: Dict[str, Any], run_id: str):
    """
    graph: {
      "nodes": {"name": {"func": "extract", "config":{}}},
      "edges": {"extract": [{"to":"check_complexity","when":"..."} , {"to":"detect_issues"}], ...},
      "entry": "extract"
    }
    """
    state = dict(initial_state or {})
    log: List[Dict[str, Any]] = []
    status = "running"
    store.save_run(run_id, {"run_id": run_id, "state": state, "status": status, "log": log, "graph_id": graph.get("graph_id")})
    current = graph.get("entry")
    max_steps = graph.get("max_steps", 200)
    steps = 0

    while current and steps < max_steps:
        steps += 1
        node_spec = graph["nodes"].get(current)
        if not node_spec:
            log.append({"node": current, "error": "node not found"})
            break
        func = node_spec.get("callable")
        config = node_spec.get("config", {})

        # Call node (support both sync and async)
        try:
            res = func(state, config)
            if asyncio.iscoroutine(res):
                res = await res
        except Exception as e:
            log.append({"node": current, "error": str(e)})
            status = "failed"
            break

        # res expected to be {"state":state, "log": "...", optionally "_next": "node"}
        if isinstance(res, dict):
            state = res.get("state", state)
            entry_log = res.get("log", "")
            log.append({"node": current, "log": entry_log, "step": steps})
        else:
            log.append({"node": current, "log": f"node returned {type(res)}", "step": steps})

        # Save intermediate state
        store.update_run(run_id, {"state": state, "log": log})

        # determine next node
        next_node = None
        edges = graph.get("edges", {}).get(current)
        if isinstance(edges, str):
            next_node = edges
        elif isinstance(edges, list):
            # edges is list of dicts {"to": "node", "when": "state['x']>0"}
            for e in edges:
                cond = e.get("when")
                if cond is None or cond == "":
                    # unconditional -> use it only if nothing else matches later
                    candidate = e.get("to")
                    if next_node is None:
                        next_node = candidate
                else:
                    if eval_condition(cond, state):
                        next_node = e.get("to")
                        break
        elif isinstance(edges, dict):
            # single mapping like {"to": "next", "when": "state['score'] > 0.8"}
            cond = edges.get("when")
            if cond is None or cond == "" or eval_condition(cond, state):
                next_node = edges.get("to")

        # allow node to override next via state key "_next_node"
        override = state.get("_next")
        if override:
            next_node = override
            state.pop("_next", None)

        # loop control: if node set state["_loop_break"] = True, stop loop
        if state.get("_loop_break"):
            break

        current = next_node

        store.update_run(run_id, {"state": state, "log": log})

    # end while
    final_status = "completed" if steps < max_steps else "max_steps_reached"
    store.update_run(run_id, {"state": state, "status": final_status, "log": log})
    return {"state": state, "log": log, "status": final_status}
