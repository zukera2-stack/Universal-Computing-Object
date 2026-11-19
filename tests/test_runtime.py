import unittest
from unittest.mock import patch
from uco_demo import CAP, checked_add
from uco_demo.unified import add,value
from uco_demo.runtime import Runtime,demo

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.p={"schema_version":"uco.graph.device.v0.1","device_id":"home","lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}
        self.devices=[{"passport":self.p,"cost":3},{"passport":dict(self.p,device_id="server",lanes=8),"cost":1}]
        self.root=add(add(value(2),value(3)),add(value(4),value(5)))
    def runtime(self): return Runtime(self.devices,b"k"*32)
    def test_end_to_end(self):
        r=self.runtime()
        with patch("uco_demo.unified.checked_add",wraps=checked_add) as op:
            out=r.run(self.root,[CAP],availability=[["home"],["home","server"],["server"]])
            self.assertEqual(op.call_count,3)
        self.assertEqual(out["result"],value(14))
        self.assertEqual(out["executed"],3)
        self.assertEqual(out["transfers"],1)
        self.assertEqual([t["device"] for t in out["trace"]],["home","home","server"])
        self.assertEqual([t["reused"] for t in out["trace"]],[0,1,2])
        self.assertEqual(len({t["logical_hash"] for t in out["trace"]}),1)
        self.assertNotEqual(out["trace"][0]["physical_hash"],out["trace"][-1]["physical_hash"])
        self.assertEqual(r.memory.get(out["root_key"]),self.root)
        self.assertEqual(r.memory.get(out["result_key"]),value(14))
    def test_automatic_choice(self):
        out=self.runtime().run(self.root,[CAP])
        self.assertEqual([t["device"] for t in out["trace"]],["server"]*3)
        self.assertEqual(out["transfers"],0)
    def test_incompatible(self):
        self.devices[1]["passport"]["max_items"]=1
        out=self.runtime().run(self.root,[CAP])
        self.assertEqual([t["device"] for t in out["trace"]],["home"]*3)
    def test_fail_closed(self):
        r=self.runtime()
        with self.assertRaises(ValueError): r.run(self.root,[])
        with self.assertRaises(ValueError): r.run(self.root,[CAP],availability=[[]])
        with self.assertRaises(ValueError): r.run(self.root,[CAP],availability=[["home"],[]])
    def test_deterministic(self):
        self.assertEqual(demo(),demo())
    def test_literal(self):
        self.assertEqual(self.runtime().run(value(7),[CAP])["result"],value(7))
