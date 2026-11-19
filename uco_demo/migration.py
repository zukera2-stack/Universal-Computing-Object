"""Authenticated portable checkpoints; simulated devices share a trust key."""
import hashlib
import hmac
import json
from . import fields, require, integer, digest
from .unified import SCHEMA, MAX_NODES, compile_program, evaluate_prefix, validate, value

def logical_plan(plan):
    # Postorder node identities and operands survive changes of lane placement.
    return {"version":"uco.logical.add.v1","object_hash":plan["object_hash"],
            "nodes":[n["inputs"] for n in plan["nodes"]],"output":plan["output"]}

def mac(body,key):
    require(type(key) is bytes and len(key)>=32,"migration key must be at least 32 bytes")
    return hmac.new(key,json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode(),hashlib.sha256).hexdigest()

def advance(root,passport,grants,key,steps=None,checkpoint=None):
    plan=compile_program(root,passport,grants)
    logical_hash=digest(logical_plan(plan))
    total=len(plan["nodes"])
    values=[]
    # Validate key even when computation finishes without a checkpoint.
    require(type(key) is bytes and len(key)>=32,"invalid migration key")
    if checkpoint is not None:
        fields(checkpoint,"schema type op payload children")
        require(checkpoint["schema"]==SCHEMA and checkpoint["type"]=="state" and checkpoint["op"]=="portable-checkpoint","invalid checkpoint")
        p=checkpoint["payload"]
        fields(p,"logical_hash cursor mac")
        require(type(p["mac"]) is str and len(p["mac"])==64 and all(c in "0123456789abcdef" for c in p["mac"]),"invalid MAC")
        require(p["logical_hash"]==logical_hash,"logical program mismatch")
        cursor=integer(p["cursor"],0,total)
        require(type(checkpoint["children"]) is list and len(checkpoint["children"])==cursor,"invalid checkpoint length")
        for child in checkpoint["children"]:
            # Reject non-value structures before hashing; no replay.
            fields(child,"schema type op payload children")
            require(child["op"]=="value","invalid checkpoint value")
            validate(child)
        body={**checkpoint,"payload":{"logical_hash":logical_hash,"cursor":cursor}}
        require(hmac.compare_digest(mac(body,key),p["mac"]),"checkpoint authentication failed")
        values=[value(v["payload"]) for v in checkpoint["children"]]
    start=len(values)
    count=total-start if steps is None else integer(steps,0,MAX_NODES)
    stop=min(total,start+count)
    resolve=evaluate_prefix(plan,values,stop)
    if stop==total:
        obj=value(resolve(plan["output"]))
    else:
        obj={"schema":SCHEMA,"type":"state","op":"portable-checkpoint",
             "payload":{"logical_hash":logical_hash,"cursor":stop},"children":values}
        obj["payload"]["mac"]=mac(obj,key)
    return {"object":obj,"executed":stop-start,"reused":start,
            "logical_hash":logical_hash,"physical_hash":digest(plan)}
