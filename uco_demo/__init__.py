"""Stage 01 simulated specialization."""
import hashlib
import json

CAP = "compute.vector.add.i32"
OP = "vector.add.i32"
LIMIT = 65536

def require(condition, message):
    if not condition:
        raise ValueError(message)

def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()), "invalid fields")

def integer(value, low, high):
    require(type(value) is int and low <= value <= high, "integer out of bounds")
    return value

def identity(value):
    require(type(value) is str and 0 < len(value) <= 128, "invalid identity")

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def specialize(obj, device, grants):
    fields(obj, "schema_version object_id operation inputs requirements requested_capabilities")
    fields(device, "schema_version device_id device_kind interface_version operations capabilities max_items strategy")
    require(obj["schema_version"] == "uco.object.v0.1", "unsupported object schema")
    require(device["schema_version"] == "uco.device.v0.1", "unsupported device schema")
    identity(obj["object_id"])
    identity(device["device_id"])
    fields(obj["operation"], "opcode semantics")
    require(obj["operation"] == {"opcode": OP, "semantics": "checked-int32"}, "unsupported operation")
    require(device["device_kind"] == "simulated" and device["interface_version"] == "uco.vector.v0.1", "unsupported device")
    require(device["strategy"] in ("scalar", "chunked"), "unsupported strategy")
    require(device["operations"] == [OP] and device["capabilities"] == [CAP], "unsupported device capabilities")
    require(obj["requested_capabilities"] == [CAP], "unsupported requested capabilities")
    require(type(grants) in (list, tuple) and all(type(g) is str and g == CAP for g in grants) and CAP in grants, "missing or invalid grant")
    fields(obj["requirements"], "max_items deterministic")
    require(obj["requirements"]["deterministic"] is True, "determinism required")
    limit = min(integer(obj["requirements"]["max_items"], 1, LIMIT), integer(device["max_items"], 1, LIMIT))
    fields(obj["inputs"], "a b")
    a, b = obj["inputs"]["a"], obj["inputs"]["b"]
    require(type(a) is list and type(b) is list and len(a) == len(b) <= limit, "invalid vector lengths")
    a, b = tuple(integer(x, -2**31, 2**31-1) for x in a), tuple(integer(x, -2**31, 2**31-1) for x in b)
    plan = {"strategy": device["strategy"], "object_hash": digest(obj), "device_hash": digest(device), "max_items": limit}
    plan["plan_hash"] = digest(plan)
    return plan, a, b

def checked_add(a, b):
    return integer(a+b, -2**31, 2**31-1)

def run(obj, device, grants):
    plan, a, b = specialize(obj, device, grants)
    if plan["strategy"] == "scalar":
        result = [checked_add(x, y) for x, y in zip(a, b)]
    else:
        result = []
        for start in range(0, len(a), 4):
            result.extend(checked_add(a[i], b[i]) for i in range(start, min(start+4, len(a))))
    return {"plan": plan, "result": result}
