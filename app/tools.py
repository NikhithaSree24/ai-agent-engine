# Tool registry: simple dictionary of callables that nodes can call.
from typing import Callable, Dict, Any
from textwrap import shorten

TOOLS: Dict[str, Callable[..., Dict[str, Any]]] = {}

def register_tool(name: str):
    def deco(fn):
        TOOLS[name] = fn
        return fn
    return deco

# Example tools for code-review style workflow:
@register_tool("extract_functions")
def extract_functions(code: str, **kwargs):
    # Simple heuristic: split by "def " etc. This is purely illustrative.
    funcs = []
    lines = code.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("def "):
            name = ln.strip().split("(")[0].replace("def ", "")
            snippet = "\n".join(lines[max(0, i-2): min(len(lines), i+10)])
            funcs.append({"name": name, "snippet": shorten(snippet, width=300)})
    return {"functions": funcs, "function_count": len(funcs)}

@register_tool("check_complexity")
def check_complexity(func_snippet: str, **kwargs):
    # Fake complexity metric: count lines and nested indentation levels
    lines = func_snippet.splitlines()
    line_count = len(lines)
    max_indent = 0
    for ln in lines:
        stripped = ln.lstrip()
        indent = len(ln) - len(stripped)
        if indent > max_indent:
            max_indent = indent
    # score 1 (good) - 10 (bad)
    score = min(10, max(1, int(line_count / 2) + int(max_indent / 4)))
    return {"complexity_score": score, "line_count": line_count, "max_indent": max_indent}

@register_tool("detect_issues")
def detect_issues(snippet: str, **kwargs):
    issues = []
    if "TODO" in snippet:
        issues.append("TODO comment found")
    if "print(" in snippet:
        issues.append("debug print found")
    if "eval(" in snippet:
        issues.append("use of eval")
    return {"issues": issues, "issue_count": len(issues)}

@register_tool("suggest_improvements")
def suggest_improvements(snippet: str, complexity_score: int = 0, **kwargs):
    suggestions = []
    if complexity_score > 6:
        suggestions.append("Refactor into smaller functions; try to reduce nesting.")
    if "print(" in snippet:
        suggestions.append("Remove prints; use logging.")
    if "TODO" in snippet:
        suggestions.append("Address TODOs before finalizing.")
    if not suggestions:
        suggestions.append("Looks good; consider adding docstrings.")
    return {"suggestions": suggestions}
