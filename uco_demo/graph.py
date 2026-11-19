"""Lower vector addition to a bounded DAG of generic checked-add primitives."""
from . import fields, require, integer, identity, digest, specialize, checked_add, CAP, LIMIT, OP

def compile_graph(obj, passport, grants):
    fields(passport, "schema_version device_id lanes max_items primitives")
    require(passport["schema_version"] == "uco.graph.device.v0.1", "unsupported schema")
    identity(passport["device_id"])
    require(passport["primitives"] == ["add.i32.checked"], "unsupported primitives")
    lanes = integer(passport["lanes"], 1, 64)
    limit = integer(passport["max_items"], 1, LIMIT)
    # Reuse Stage 01 object validation, not its target executor.
    _, a, b = specialize(obj, {"schema_version":"uco.device.v0.1",
        "device_id":passport["device_id"], "device_kind":"simulated",
        "interface_version":"uco.vector.v0.1", "operations":[OP],
        "capabilities":[CAP], "max_items":limit, "strategy":"scalar"}, grants)
    nodes = [{"id":i, "op":"add.i32.checked", "inputs":[["a",i],["b",i]],
              "batch":i//lanes, "lane":i%lanes} for i in range(len(a))]
    graph = {"schema":"uco.graph.v0.1", "object_hash":digest(obj),
             "passport_hash":digest(passport), "nodes":nodes,
             "outputs":list(range(len(a)))}
    graph["graph_hash"] = digest(graph)
    return graph, a, b

def run_graph(obj, passport, grants):
    graph, a, b = compile_graph(obj, passport, grants)
    # Only internally produced graphs are executable. No eval or external graph input.
    inputs = {"a":a,"b":b}
    values = {}
    primitives = {"add.i32.checked":checked_add}
    for node in graph["nodes"]:
        args = [inputs[name][index] for name,index in node["inputs"]]
        values[node["id"]] = primitives[node["op"]](*args)
    return {"graph":graph,"result":[values[i] for i in graph["outputs"]]}
