"""Bounded recursive scalar composition, lowered to one primitive DAG."""
from . import CAP, digest, fields, identity, integer, require, checked_add

MAX_NODES = 4096
MAX_DEPTH = 32

def compile_composition(obj, passport, grants):
    fields(obj, "schema_version object_id root requested_capabilities")
    require(obj["schema_version"] == "uco.composition.v0.1", "unsupported object schema")
    identity(obj["object_id"])
    require(obj["requested_capabilities"] == [CAP], "unsupported capability")
    require(type(grants) in (list, tuple) and bool(grants) and all(type(g) is str and g == CAP for g in grants), "invalid grant")
    fields(passport, "schema_version device_id lanes max_items primitives")
    require(passport["schema_version"] == "uco.graph.device.v0.1", "unsupported passport")
    identity(passport["device_id"])
    lanes = integer(passport["lanes"], 1, 64)
    limit = min(MAX_NODES, integer(passport["max_items"], 1, 65536))
    require(passport["primitives"] == ["add.i32.checked"], "unsupported primitives")
    nodes = []
    active = set()
    visited = 0
    def lower(expr, depth):
        nonlocal visited
        require(depth <= MAX_DEPTH and visited < limit, "composition budget exceeded")
        visited += 1
        fields(expr, "kind value" if type(expr) is dict and expr.get("kind") == "literal" else "kind children")
        require(id(expr) not in active, "cyclic composition")
        active.add(id(expr))
        try:
            if expr["kind"] == "literal":
                return {"literal":integer(expr["value"], -2**31, 2**31-1)}, -1
            require(expr["kind"] == "add" and type(expr["children"]) is list and len(expr["children"]) == 2, "unsupported composition")
            left, lb = lower(expr["children"][0], depth+1)
            right, rb = lower(expr["children"][1], depth+1)
            earliest = max(lb, rb)+1
            occupied = {(n["batch"], n["lane"]) for n in nodes}
            slot = earliest*lanes
            while divmod(slot, lanes) in occupied:
                slot += 1
            batch, lane = divmod(slot, lanes)
            index = len(nodes)
            nodes.append({"id":index, "op":"add.i32.checked", "inputs":[left,right], "batch":batch, "lane":lane})
            return {"ref":index}, batch
        finally:
            active.remove(id(expr))
    output, _ = lower(obj["root"], 0)
    graph = {"schema":"uco.composition.graph.v0.1", "object_hash":digest(obj), "passport_hash":digest(passport), "nodes":nodes, "output":output}
    graph["graph_hash"] = digest(graph)
    return graph

def run_composition(obj, passport, grants):
    graph = compile_composition(obj, passport, grants)
    values = {}
    def resolve(operand):
        return operand["literal"] if "literal" in operand else values[operand["ref"]]
    for node in graph["nodes"]:
        values[node["id"]] = checked_add(*(resolve(x) for x in node["inputs"]))
    return {"graph":graph, "result":resolve(graph["output"])}
