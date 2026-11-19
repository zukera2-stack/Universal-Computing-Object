import copy
import json
import unittest
from unittest.mock import patch
from uco_demo import CAP, checked_add
from uco_demo.unified import add,value
from uco_demo.migration import advance

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.root=add(add(value(2),value(3)),add(value(4),value(5)))
        self.a={"schema_version":"uco.graph.device.v0.1","device_id":"home","lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}
        self.b=dict(self.a,device_id="server",lanes=8)
        self.key=b"k"*32
    def step(self,p,**kw):
        return advance(self.root,p,[CAP],self.key,**kw)
    def test_no_replay(self):
        with patch("uco_demo.unified.checked_add",wraps=checked_add) as op:
            a=self.step(self.a,steps=2)
            self.assertEqual(op.call_count,2)
            state=json.loads(json.dumps(a["object"]))
            b=self.step(self.b,checkpoint=state)
            self.assertEqual(op.call_count,3)
        self.assertEqual(b["object"],value(14))
        self.assertEqual((b["reused"],b["executed"]),(2,1))
        self.assertEqual(a["logical_hash"],b["logical_hash"])
        self.assertNotEqual(a["physical_hash"],b["physical_hash"])
        self.assertEqual(self.step(self.b)["object"],b["object"])
    def test_tamper(self):
        state=self.step(self.a,steps=1)["object"]
        for mutate in (lambda s:s["children"][0].update(payload=99),lambda s:s["payload"].update(cursor=0),lambda s:s["payload"].update(mac="0"*64)):
            bad=copy.deepcopy(state)
            mutate(bad)
            with self.assertRaises(ValueError): self.step(self.b,checkpoint=bad)
        with self.assertRaises(ValueError): advance(self.root,self.b,[CAP],b"x"*32,checkpoint=state)
        with self.assertRaises(ValueError): advance(add(value(1),value(2)),self.b,[CAP],self.key,checkpoint=state)
        with self.assertRaises(ValueError): advance(self.root,self.b,[],self.key,checkpoint=state)
    def test_multiple_hops(self):
        state=self.step(self.a,steps=0)["object"]
        state=self.step(self.b,steps=1,checkpoint=state)["object"]
        state=self.step(self.a,steps=1,checkpoint=state)["object"]
        self.assertEqual(self.step(self.b,checkpoint=state)["object"],value(14))
    def test_incompatible_target(self):
        state=self.step(self.a,steps=1)["object"]
        with self.assertRaises(ValueError): self.step(dict(self.b,max_items=1),checkpoint=state)
        with self.assertRaises(ValueError): self.step(dict(self.b,primitives=[]),checkpoint=state)
