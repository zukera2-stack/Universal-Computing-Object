import copy
import unittest
from uco_demo import CAP
from uco_demo.composition import run_composition
def lit(n): return {"kind":"literal","value":n}
def add(a,b): return {"kind":"add","children":[a,b]}
class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.obj={"schema_version":"uco.composition.v0.1","object_id":"nested","root":add(add(lit(2),lit(3)),add(lit(4),lit(5))),"requested_capabilities":[CAP]}
        self.p={"schema_version":"uco.graph.device.v0.1","device_id":"sim","lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}
    def test_nested(self):
        original=copy.deepcopy(self.obj)
        a=run_composition(self.obj,self.p,[CAP])
        b=run_composition(self.obj,dict(self.p,lanes=3),[CAP])
        self.assertEqual(a["result"],14)
        self.assertEqual(b["result"],14)
        self.assertNotEqual(a["graph"]["nodes"],b["graph"]["nodes"])
        self.assertEqual(a,run_composition(self.obj,self.p,[CAP]))
        self.assertEqual(original,self.obj)
        for g in (a["graph"],b["graph"]):
            for n in g["nodes"]:
                for operand in n["inputs"]:
                    if "ref" in operand:
                        self.assertLess(g["nodes"][operand["ref"]]["batch"],n["batch"])
    def test_literal(self):
        self.obj["root"]=lit(7)
        self.assertEqual(run_composition(self.obj,self.p,[CAP])["result"],7)
    def test_rejection(self):
        for root in (lit(True),add(lit(2**31-1),lit(1)),{"kind":"unknown","children":[]},add(lit(1),lit(2))):
            self.obj["root"]=root
            with self.assertRaises(ValueError):
                run_composition(self.obj,dict(self.p,max_items=1),[CAP]) if root["kind"]=="add" and root["children"][0]==lit(1) else run_composition(self.obj,self.p,[CAP])
        self.obj["root"]=add(lit(1),lit(2))
        with self.assertRaises(ValueError): run_composition(self.obj,self.p,[])
    def test_cycle_and_depth(self):
        root=add(lit(1),lit(2))
        root["children"][0]=root
        self.obj["root"]=root
        with self.assertRaises(ValueError): run_composition(self.obj,self.p,[CAP])
        root=lit(0)
        for _ in range(34): root=add(root,lit(1))
        self.obj["root"]=root
        with self.assertRaises(ValueError): run_composition(self.obj,self.p,[CAP])
