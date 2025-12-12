# Simple in-memory store for graphs and runs (thread-safe-ish with locks)
import threading
from typing import Dict, Any

class Store:
    def __init__(self):
        self._graphs = {}
        self._runs = {}
        self._lock = threading.Lock()

    def save_graph(self, graph_id: str, graph: Dict[str, Any]):
        with self._lock:
            self._graphs[graph_id] = graph

    def get_graph(self, graph_id: str):
        with self._lock:
            return self._graphs.get(graph_id)

    def save_run(self, run_id: str, run: Dict[str, Any]):
        with self._lock:
            self._runs[run_id] = run

    def get_run(self, run_id: str):
        with self._lock:
            return self._runs.get(run_id)

    def update_run(self, run_id: str, update: Dict[str, Any]):
        with self._lock:
            r = self._runs.get(run_id)
            if not r:
                return
            r.update(update)
            self._runs[run_id] = r

store = Store()
