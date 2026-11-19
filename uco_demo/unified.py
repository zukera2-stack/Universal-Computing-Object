"""Unified tagged object envelope and replay-validated execution checkpoints."""
from copy import deepcopy
from . import CAP, fields, identity, integer, require, digest, checked_add

SCHEMA = "uco.unified.v0.1"
MAX_NODES = 4096
MAX_DEPTH = 32

def value(n):
    return {"schema":SCHEMA,"type":"i32","op":"value","payload":integer(n,-2**31,2**31-1),"children":[]}

def add(a,b):
    return {"schema":SCHEMA,"type":"i32","op":"add","payload":None,"children":[a,b]}

def validate(root):
    active=set()
    count=0
    def walk(node,depth):
        nonlocal count
        require(depth<=MAX_DEPTH and count<MAX_NODES,"object budget exceeded")
        count+=1
        fields(node,"schema type op payload children")
        require(node["schema"]==SCHEMA and node["type"]=="i32","unsupported object type")
        require(type(node["children"]) is list,"invalid children")
        require(id(node) not in active,"cycle")
        active.add(id(node))
        try:
            if node["op"]=="value":
                require(not node["children"],"value has children")
                integer(node["payload"],-2**31,2**31-1)
            else:
                require(node["op"]=="add" and node["payload"] is None and len(node["children"])==2,"invalid operation")
                for child in node["children"]: walk(child,depth+1)
        finally:
            active.remove(id(node))
    walk(root,0)

def compile_program(root,passport,grants):
    validate(root)
    fields(passport,"schema_version device_id lanes max_items primitives")
    require(passport["schema_version"]=="uco.graph.device.v0.1","unsupported passport")
    identity(passport["device_id"])
    lanes=integer(passport["lanes"],1,64)
    limit=integer(passport["max_items"],1,65536)
    require(passport["primitives"]==["add.i32.checked"],"unsupported primitives")
    require(type(grants) in (list,tuple) and all(type(g) is str and g==CAP for g in grants) and CAP in grants,"invalid grant")
    nodes=[]
    occupied=set()
    def lower(node):
        if node["op"]=="value": return {"literal":node["payload"]},-1
        a,ab=lower(node["children"][0])
        b,bb=lower(node["children"][1])
        require(len(nodes)<limit,"device operation budget exceeded")
        slot=(max(ab,bb)+1)*lanes
        while divmod(slot,lanes) in occupied: slot+=1
        batch,lane=divmod(slot,lanes)
        occupied.add((batch,lane))
        idx=len(nodes)
        nodes.append({"inputs":[a,b],"batch":batch,"lane":lane})
        return {"ref":idx},batch
    output,_=lower(root)
    return {"object_hash":digest(root),"passport_hash":digest(passport),"nodes":nodes,"output":output}

def evaluate_prefix(plan, values, stop):
    def resolve(arg):
        return arg["literal"] if "literal" in arg else values[arg["ref"]]["payload"]
    for node in plan["nodes"][len(values):stop]:
        values.append(value(checked_add(*(resolve(a) for a in node["inputs"]))))
    return resolve

def run(root,passport,grants,steps=None,checkpoint=None):
    """Return a unified result or checkpoint; checkpoints are validated by replay."""
    plan=compile_program(root,passport,grants)
    total=len(plan["nodes"])
    values=[]
    if checkpoint is not None:
        fields(checkpoint,"schema type op payload children")
        require(checkpoint["schema"]==SCHEMA and checkpoint["type"]=="state" and checkpoint["op"]=="checkpoint","bad checkpoint")
        fields(checkpoint["payload"],"object_hash plan_hash cursor")
        p=checkpoint["payload"]
        require(p["object_hash"]==plan["object_hash"] and p["plan_hash"]==digest(plan),"checkpoint mismatch")
        cursor=integer(p["cursor"],0,total)
        require(type(checkpoint["children"]) is list and len(checkpoint["children"])==cursor,"bad checkpoint values")
        for child in checkpoint["children"]:
            validate(child)
            require(child["op"]=="value","checkpoint requires values")
        evaluate_prefix(plan,values,cursor)
        require(values==checkpoint["children"],"checkpoint replay mismatch")
    count=total-len(values) if steps is None else integer(steps,0,MAX_NODES)
    stop=min(total,len(values)+count)
    resolve=evaluate_prefix(plan,values,stop)
    if stop==total:
        return value(resolve(plan["output"]))
    return {"schema":SCHEMA,"type":"state","op":"checkpoint","payload":{"object_hash":plan["object_hash"],"plan_hash":digest(plan),"cursor":stop},"children":deepcopy(values)}
