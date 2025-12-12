from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union

class NodeSpec(BaseModel):
    name: str
    # name of the node function (string). The engine will look up the node from a registry.
    func: str
    # optional config passed to node
    config: Optional[Dict[str, Any]] = {}

class EdgeWhen(BaseModel):
    when: Optional[str] = None  # Python expression evaluated with `state` in safe globals
    to: str

class GraphCreateRequest(BaseModel):
    nodes: List[NodeSpec]
    # edges mapping node_name -> list of EdgeWhen or single string
    edges: Dict[str, Union[str, List[EdgeWhen], EdgeWhen]]

class GraphCreateResponse(BaseModel):
    graph_id: str

class RunRequest(BaseModel):
    graph_id: str
    initial_state: Optional[Dict[str, Any]] = {}

class RunResponse(BaseModel):
    run_id: str
    final_state: Optional[Dict[str, Any]] = None
    log: List[Dict[str, Any]] = []

class RunStateResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]
    status: str
    log: List[Dict[str, Any]]
