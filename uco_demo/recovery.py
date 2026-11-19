"""Single-supervisor, disk-backed recovery from real local worker termination."""
import multiprocessing as mp
import os
import json
import hmac
import secrets
import tempfile
from pathlib import Path
from . import require, integer, digest, fields
from .unified import compile_program, validate, MAX_NODES
from .migration import advance, mac, logical_plan

def save(path, body, key):
    path=Path(path)
    packet={"body":body,"mac":mac(body,key)}
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".uco-")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(packet,f,sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
        if os.name=="posix":
            directory=os.open(path.parent,os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load(path,key):
    with open(path,"rb") as f:
        raw=f.read(4_000_001)
    require(len(raw)<=4_000_000,"checkpoint too large")
    packet=json.loads(raw)
    fields(packet,"body mac")
    require(type(packet["mac"]) is str and len(packet["mac"])==64 and all(c in "0123456789abcdef" for c in packet["mac"]),"bad authentication")
    require(hmac.compare_digest(mac(packet["body"],key),packet["mac"]),"journal authentication failed")
    return packet["body"]

def worker(conn,path,root,passport,grants,key,job,quantum):
    # Only the supervisor grants one slice at a time.
    from . import unified
    primitive=unified.checked_add
    calls=0
    def counted(a,b):
        nonlocal calls
        calls+=1
        return primitive(a,b)
    unified.checked_add=counted
    try:
        while conn.recv()=="step":
            prior=load(path,key)
            require(prior["job"]==job and prior["status"]=="pending","wrong job or status")
            calls=0
            result=advance(root,passport,grants,key,steps=quantum,checkpoint=prior["state"])
            require(result["reused"]==prior["committed"] and calls==result["executed"],"progress mismatch")
            obj=result["object"]
            body={"job":job,"committed":prior["committed"]+calls,
                  "status":"pending" if obj["type"]=="state" else "done",
                  "state":obj,"worker":passport["device_id"],"pid":os.getpid(),
                  "calls":calls,"logical_hash":result["logical_hash"]}
            save(path,body,key)
            conn.send({"ok":True,"committed":body["committed"]})
    except EOFError:
        pass
    except Exception as exc:
        try: conn.send({"ok":False,"error":str(exc)})
        except (OSError,EOFError): pass
    finally: conn.close()

def supervise(root,devices,grants,key,directory,quantum=1,kill_after=None,timeout=15):
    """Fresh job only; one supervisor, one worker at a time, trusted directory."""
    require(type(devices) is list and len(devices)>=2,"two devices required")
    integer(quantum,1,MAX_NODES)
    integer(timeout,1,120)
    plans=[compile_program(root,p,grants) for p in devices]
    require(len({p["device_id"] for p in devices})==len(devices),"duplicate device")
    logical=digest(logical_plan(plans[0]))
    require(all(digest(logical_plan(p))==logical for p in plans),"incompatible plans")
    total=len(plans[0]["nodes"])
    if kill_after is not None: integer(kill_after,1,max(1,total-1))
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/"checkpoint.json"
    # Exclusive creation prevents accidental overwrite of another job.
    with open(path,"x",encoding="utf-8"): pass
    job=secrets.token_hex(16)
    save(path,{"job":job,"committed":0,"status":"pending","state":None,
               "worker":None,"pid":None,"calls":0,"logical_hash":logical},key)
    ctx=mp.get_context("spawn")
    trace=[]
    failures=[]
    index=0
    killed=False
    while index<len(devices):
        parent,child=ctx.Pipe()
        process=ctx.Process(target=worker,args=(child,str(path),root,devices[index],grants,key,job,quantum))
        process.start()
        child.close()
        try:
            while True:
                before=load(path,key)
                try:
                    parent.send("step")
                    if not parent.poll(timeout):
                        raise TimeoutError("worker timeout")
                    reply=parent.recv()
                except (EOFError,OSError,TimeoutError):
                    if process.is_alive(): process.kill()
                    process.join(timeout)
                    require(not process.is_alive(),"worker did not stop")
                    failures.append({"pid":process.pid,"exitcode":process.exitcode})
                    break
                require(reply["ok"],reply.get("error","worker error"))
                after=load(path,key)
                require(after["job"]==job and after["logical_hash"]==logical,"journal mismatch")
                require(after["committed"]==before["committed"]+after["calls"],"invalid progress")
                trace.append({"pid":after["pid"],"device":after["worker"],"calls":after["calls"],"reused":before["committed"],"committed":after["committed"]})
                if after["status"]=="done":
                    validate(after["state"])
                    return {"result":after["state"],"trace":trace,"failures":failures,
                            "committed":after["committed"],"journal":str(path)}
                if kill_after is not None and not killed and after["committed"]>=kill_after:
                    process.kill()
                    process.join(timeout)
                    require(not process.is_alive() and process.exitcode!=0,"fault injection failed")
                    failures.append({"pid":process.pid,"exitcode":process.exitcode})
                    killed=True
                    break
        finally:
            parent.close()
            if process.is_alive(): process.terminate()
            process.join(timeout)
            if process.is_alive():
                process.kill()
                process.join(timeout)
            require(not process.is_alive(),"worker cleanup failed")
        index+=1
    raise RuntimeError("all workers exhausted")
