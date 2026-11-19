import copy
import json
import unittest
from uco_demo import CAP
from uco_demo.unified import value,add,run,compile_program

class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.root=add(add(value(2),value(3)),add(value(4),value(5)))
        self.p={"schema_version":"uco.graph.device.v0.1","device_id":"sim","lanes":2,"max_items":1024,"primitives":["add.i32.checked"]}
    def test_closed_result(self):
        initial=copy.deepcopy(self.root)
        result=run(self.root,self.p,[CAP])
        self.assertEqual(result,value(14))
        self.assertEqual(run(add(result,value(1)),self.p,[CAP]),value(15))
        self.assertEqual(initial,self.root)
    def test_checkpoint(self):
        state=run(self.root,self.p,[CAP],steps=1)
        self.assertEqual(state["type"],"state")
        state=json.loads(json.dumps(state))
        state=run(self.root,self.p,[CAP],steps=1,checkpoint=state)
        self.assertEqual(run(self.root,self.p,[CAP],checkpoint=state),value(14))
        state["children"][0]["payload"]=999
        with self.assertRaises(ValueError): run(self.root,self.p,[CAP],checkpoint=state)
    def test_passports(self):
        other=dict(self.p,lanes=1)
        self.assertNotEqual(compile_program(self.root,self.p,[CAP]),compile_program(self.root,other,[CAP]))
        self.assertEqual(run(self.root,self.p,[CAP]),run(self.root,other,[CAP]))
        state=run(self.root,self.p,[CAP],steps=1)
        with self.assertRaises(ValueError): run(self.root,other,[CAP],checkpoint=state)
    def test_rejection(self):
        for root in (add(value(2147483647),value(1)),dict(value(1),payload=True),dict(value(1),extra=1),dict(value(1),op="unknown")):
            with self.assertRaises(ValueError): run(root,self.p,[CAP])
        with self.assertRaises(ValueError): run(self.root,self.p,[])
        cycle=add(value(1),value(2))
        cycle["children"][0]=cycle
        with self.assertRaises(ValueError): run(cycle,self.p,[CAP])
    def test_zero_steps(self):
        state=run(self.root,self.p,[CAP],steps=0)
        self.assertEqual(state["payload"]["cursor"],0)
        self.assertEqual(run(self.root,self.p,[CAP],checkpoint=state),value(14))
        self.assertEqual(run(value(7),self.p,[CAP]),value(7))
