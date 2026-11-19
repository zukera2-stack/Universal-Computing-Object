import copy
import unittest
from uco_demo import CAP, run
from uco_demo.graph import run_graph
from uco_demo.__main__ import load

class GraphTests(unittest.TestCase):
    def setUp(self):
        self.obj = load("examples/vector_add.json")
        self.device = {"schema_version":"uco.graph.device.v0.1","device_id":"generic",
                       "lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}

    def test_unseen_widths(self):
        self.obj["inputs"] = {"a":list(range(17)), "b":[2]*17}
        self.obj["requirements"]["max_items"] = 17
        original = copy.deepcopy(self.obj)
        for width in (1,2,3,5,7,16,64):
            p = dict(self.device, lanes=width)
            result = run_graph(self.obj,p,[CAP])
            self.assertEqual(result["result"],list(range(2,19)))
            self.assertEqual(result,run_graph(self.obj,p,[CAP]))
            for i,node in enumerate(result["graph"]["nodes"]):
                self.assertEqual((node["batch"],node["lane"]),divmod(i,width))
        self.assertEqual(original,self.obj)

    def test_distinct_graphs(self):
        a = run_graph(self.obj,self.device,[CAP])
        b = run_graph(self.obj,dict(self.device,lanes=2),[CAP])
        self.assertNotEqual(a["graph"]["nodes"],b["graph"]["nodes"])
        self.assertEqual(a["result"],b["result"])
        self.assertEqual(a["result"],run(self.obj,load("examples/device_scalar.json"),[CAP])["result"])

    def test_rejection(self):
        for change in ({"lanes":0},{"lanes":True},{"lanes":65},{"primitives":[]},{"code":"bad"},{"max_items":2}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_graph(self.obj,dict(self.device,**change),[CAP])
        with self.assertRaises(ValueError):
            run_graph(self.obj,self.device,[])
        self.obj["inputs"]["a"][0]=2**31-1
        with self.assertRaises(ValueError):
            run_graph(self.obj,self.device,[CAP])
