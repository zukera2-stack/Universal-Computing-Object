"""Deterministic three-tier placement simulation, not a physical cache."""
from dataclasses import dataclass
from . import require, integer, digest
from .unified import validate

@dataclass(frozen=True)
class Tier:
    capacity: int
    latency: int
    rent: int

TIERS = (Tier(8,1,3), Tier(16,5,1), Tier(64,20,0))
MOVE_UNIT = 2

class Memory:
    def __init__(self, policy="adaptive", tiers=TIERS):
        require(policy in ("adaptive","lru"),"unknown policy")
        require(type(tiers) is tuple and len(tiers)==3,"three tiers required")
        for t in tiers:
            require(isinstance(t,Tier),"invalid tier")
            integer(t.capacity,1,1000000)
            integer(t.latency,1,1000000)
            integer(t.rent,0,1000000)
        self.policy=policy
        self.tiers=tiers
        self.objects={}
        self.tick=0
        self.access_cost=self.move_cost=self.storage_cost=self.missed_deadlines=0
        self.moves=0

    def used(self,tier):
        return sum(r["size"] for r in self.objects.values() if r["tier"]==tier)

    def put(self,obj,size,deadline):
        validate(obj)
        size=integer(size,1,self.tiers[2].capacity)
        deadline=integer(deadline,1,1000000)
        import json
        data=json.dumps(obj,sort_keys=True,separators=(",",":"))
        key=digest(obj)
        require(key not in self.objects,"duplicate object")
        require(self.used(2)+size<=self.tiers[2].capacity,"cold tier full")
        self.objects[key]={"data":data,"size":size,"deadline":deadline,"tier":2,"heat":0,"last":-1}
        return key

    def move(self,r,target):
        if target==r["tier"]: return
        require(self.used(target)+r["size"]<=self.tiers[target].capacity,"tier full")
        self.move_cost+=MOVE_UNIT*r["size"]*abs(target-r["tier"])
        self.moves+=1
        r["tier"]=target

    def utility(self,r,tier):
        t=self.tiers[tier]
        # Heat is a decayed access estimate in fixed-point units.
        return r["heat"]*(self.tiers[2].latency-t.latency+max(0,self.tiers[2].latency-r["deadline"])-max(0,t.latency-r["deadline"]))-8*t.rent*r["size"]

    def promote(self,r):
        for target in range(r["tier"]):
            if r["size"]>self.tiers[target].capacity: continue
            occupants=[(k,v) for k,v in self.objects.items() if v["tier"]==target]
            if self.policy=="adaptive":
                occupants.sort(key=lambda kv:(self.utility(kv[1],target)-self.utility(kv[1],r["tier"]),kv[0]))
            else:
                occupants.sort(key=lambda kv:(kv[1]["last"],kv[0]))
            victims=[]
            freed=0
            needed=max(0,self.used(target)+r["size"]-self.tiers[target].capacity)
            for _,v in occupants:
                if freed>=needed: break
                victims.append(v)
                freed+=v["size"]
            source=r["tier"]
            # Swap transaction: source space freed by promotion is counted.
            if freed<needed or self.used(source)-r["size"]+freed>self.tiers[source].capacity: continue
            cost=MOVE_UNIT*(r["size"]+freed)*abs(target-source)
            gain=self.utility(r,target)-self.utility(r,source)-sum(self.utility(v,target)-self.utility(v,source) for v in victims)
            if self.policy=="adaptive" and gain<=8*cost: continue
            r["tier"]=target
            for v in victims: v["tier"]=source
            self.move_cost+=cost
            self.moves+=1+len(victims)
            return

    def get(self,key):
        import json
        require(key in self.objects,"unknown object")
        self.tick+=1
        for r in self.objects.values(): r["heat"]=r["heat"]*7//8
        r=self.objects[key]
        latency=self.tiers[r["tier"]].latency
        self.access_cost+=latency
        self.missed_deadlines+=int(latency>r["deadline"])
        r["heat"]+=8
        r["last"]=self.tick
        self.promote(r)
        self.storage_cost+=sum(self.tiers[v["tier"]].rent*v["size"] for v in self.objects.values())
        return json.loads(r["data"])

    def metrics(self):
        return {"access":self.access_cost,"movement":self.move_cost,"storage":self.storage_cost,
                "total":self.access_cost+self.move_cost+self.storage_cost,
                "moves":self.moves,"deadline_misses":self.missed_deadlines}

def benchmark():
    from .unified import value
    scenarios={"stable_hot": [0,1,0,1]*40,
               "scan":list(range(12))*12,
               "phase_change":[0,1]*40+[8,9]*40,
               "mixed":[0,1,0,2,0,1,3,4,0,1,5,6,0,1,7,8,9,10,11]*12}
    result={}
    for name,trace in scenarios.items():
        result[name]={}
        for policy in ("adaptive","lru"):
            m=Memory(policy)
            keys=[m.put(value(i),2,5 if i<2 else 20) for i in range(12)]
            for i in trace:
                require(m.get(keys[i])==value(i),"data corruption")
                require(all(m.used(j)<=t.capacity for j,t in enumerate(m.tiers)),"capacity violation")
            result[name][policy]=m.metrics()
    return result

if __name__=="__main__":
    import json
    print(json.dumps(benchmark(),indent=2,sort_keys=True))
