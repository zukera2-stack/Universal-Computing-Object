"""One deterministic orchestration loop over the existing simulated mechanisms."""
from copy import deepcopy
import json
from . import CAP, require, integer, digest
from .unified import compile_program, validate, MAX_NODES
from .migration import advance
from .memory import Memory

class Runtime:
    def __init__(self, devices, key, quantum=1, memory=None):
        require(type(key) is bytes and len(key)>=32,"invalid key")
        require(type(devices) is list and bool(devices),"devices required")
        self.devices={}
        for d in deepcopy(devices):
            require(type(d) is dict and set(d)=={"passport","cost"},"invalid device entry")
            p=d["passport"]
            require(type(p) is dict and type(p.get("device_id")) is str,"invalid passport")
            name=p["device_id"]
            require(name not in self.devices,"duplicate device")
            integer(d["cost"],1,1000000)
            self.devices[name]=d
        self.key=key
        self.quantum=integer(quantum,1,MAX_NODES)
        self.memory=memory if memory is not None else Memory()

    def store(self,obj,deadline):
        key=digest(obj)
        if key not in self.memory.objects:
            # Model units: one unit per 256 serialized bytes, rounded up.
            size=max(1,(len(json.dumps(obj,sort_keys=True,separators=(",",":")).encode())+255)//256)
            self.memory.put(obj,size,deadline)
        return key

    def run(self,root,grants,deadline=20,availability=None):
        validate(root)
        integer(deadline,1,1000000)
        require(type(grants) in (list,tuple) and CAP in grants and all(type(x) is str and x==CAP for x in grants),"invalid grant")
        require(availability is None or type(availability) is list,"invalid availability trace")
        if availability is not None:
            for slot in availability:
                require(type(slot) is list and all(type(x) is str and x in self.devices for x in slot),"invalid availability slot")
        root_key=self.store(root,deadline)
        state=None
        trace=[]
        executed=0
        previous=None
        transfers=0
        while True:
            tick=len(trace)
            allowed=set(self.devices) if availability is None else set(availability[tick]) if tick<len(availability) else set()
            obj=self.memory.get(root_key)
            candidates=[]
            for name in sorted(allowed):
                d=self.devices[name]
                try:
                    plan=compile_program(obj,d["passport"],grants)
                except ValueError:
                    continue
                remaining=max(0,len(plan["nodes"])-executed)
                count=min(self.quantum,remaining)
                # Estimate next slice cost; switching adds modeled checkpoint overhead.
                score=count*d["cost"]+(2 if previous is not None and previous!=name else 0)
                candidates.append((score,name))
            require(bool(candidates),"no compatible available device")
            _,name=min(candidates)
            if previous is not None and previous!=name: transfers+=1
            result=advance(obj,self.devices[name]["passport"],grants,self.key,steps=self.quantum,checkpoint=state)
            require(result["reused"]==executed,"inconsistent progress")
            executed+=result["executed"]
            trace.append({"device":name,"executed":result["executed"],"reused":result["reused"],"physical_hash":result["physical_hash"],"logical_hash":result["logical_hash"]})
            if result["object"]["type"]!="state":
                result_key=self.store(result["object"],deadline)
                return {"result":self.memory.get(result_key),"result_key":result_key,"root_key":root_key,"executed":executed,"transfers":transfers,"trace":trace,"memory":self.memory.metrics()}
            # Transport boundary: serialize and reload authenticated state.
            state=json.loads(json.dumps(result["object"],sort_keys=True))
            previous=name

def demo():
    from .unified import value,add
    p={"schema_version":"uco.graph.device.v0.1","device_id":"home","lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}
    runtime=Runtime([{"passport":p,"cost":3},{"passport":dict(p,device_id="server",lanes=8),"cost":1}],b"d"*32)
    root=add(add(value(2),value(3)),add(value(4),value(5)))
    return runtime.run(root,[CAP],availability=[["home"],["home","server"],["server"]])

if __name__=="__main__":
    print(json.dumps(demo(),indent=2,sort_keys=True))
