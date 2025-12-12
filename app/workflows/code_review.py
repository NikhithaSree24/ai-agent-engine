# Example workflow nodes for Option A: Code Review Mini-Agent
from typing import Dict, Any
from app.tools import TOOLS
import asyncio

# Node functions should be async-friendly. They receive state and config.
async def node_extract(state: Dict[str, Any], config: Dict[str, Any]):
    code = state.get("code", "")
    res = TOOLS["extract_functions"](code=code)
    state.setdefault("meta", {})["extracted"] = res
    state["quality_score"] = state.get("quality_score", 0.0)
    return {"state": state, "log": f"extracted {res.get('function_count',0)} functions"}

async def node_check_complexity(state: Dict[str, Any], config: Dict[str, Any]):
    extracted = state.get("meta", {}).get("extracted", {})
    func_list = extracted.get("functions", [])
    complexities = []
    for f in func_list:
        c = TOOLS["check_complexity"](func_snippet=f["snippet"])
        complexities.append({"name": f["name"], **c})
    state.setdefault("meta", {})["complexities"] = complexities
    # simple quality score: lower complexity -> higher quality
    avg_complexity = (sum(x["complexity_score"] for x in complexities) / len(complexities)) if complexities else 1
    state["quality_score"] = max(0.0, 10 - avg_complexity) / 10
    return {"state": state, "log": f"checked complexity, avg={avg_complexity:.2f}"}

async def node_detect_issues(state: Dict[str, Any], config: Dict[str, Any]):
    extracted = state.get("meta", {}).get("extracted", {})
    func_list = extracted.get("functions", [])
    issues_by_func = []
    total_issues = 0
    for f in func_list:
        d = TOOLS["detect_issues"](snippet=f["snippet"])
        issues_by_func.append({"name": f["name"], **d})
        total_issues += d.get("issue_count", 0)
    state.setdefault("meta", {})["issues"] = issues_by_func
    # penalty to quality_score
    state["quality_score"] = max(0.0, state.get("quality_score", 0.0) - total_issues * 0.05)
    return {"state": state, "log": f"detected {total_issues} issues"}

async def node_suggest_improvements(state: Dict[str, Any], config: Dict[str, Any]):
    complexities = state.get("meta", {}).get("complexities", [])
    suggestions = []
    for c in complexities:
        s = TOOLS["suggest_improvements"](snippet="", complexity_score=c.get("complexity_score",0))
        suggestions.append({"name": c["name"], "suggestions": s["suggestions"]})
    state.setdefault("meta", {})["suggestions"] = suggestions
    # increase quality slightly for each suggestion (simulating improvements)
    state["quality_score"] = min(1.0, state.get("quality_score", 0.0) + 0.1)
    return {"state": state, "log": "suggested improvements"}

# Node registry the engine looks up
NODE_REGISTRY = {
    "extract": node_extract,
    "check_complexity": node_check_complexity,
    "detect_issues": node_detect_issues,
    "suggest_improvements": node_suggest_improvements
}
