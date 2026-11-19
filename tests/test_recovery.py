import json
import tempfile
import unittest
from pathlib import Path
from uco_demo import CAP
from uco_demo.unified import add,value
from uco_demo.recovery import supervise,load

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.root=add(add(value(2),value(3)),add(value(4),value(5)))
        p={"schema_version":"uco.graph.device.v0.1","device_id":"primary","lanes":1,"max_items":1024,"primitives":["add.i32.checked"]}
        self.devices=[p,dict(p,device_id="backup",lanes=8)]
        self.key=b"k"*32
    def test_real_kill_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            out=supervise(self.root,self.devices,[CAP],self.key,d,kill_after=2)
            self.assertEqual(out["result"],value(14))
            self.assertEqual(out["committed"],3)
            self.assertEqual(len(out["failures"]),1)
            self.assertNotEqual(out["failures"][0]["exitcode"],0)
            self.assertEqual([x["calls"] for x in out["trace"]],[1,1,1])
            self.assertEqual([x["reused"] for x in out["trace"]],[0,1,2])
            self.assertEqual([x["device"] for x in out["trace"]],["primary","primary","backup"])
            self.assertNotEqual(out["trace"][0]["pid"],out["trace"][-1]["pid"])
            self.assertEqual(load(out["journal"],self.key)["state"],value(14))
    def test_normal_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            out=supervise(self.root,self.devices,[CAP],self.key,d)
            self.assertEqual(out["failures"],[])
            self.assertEqual(out["result"],value(14))
            path=Path(out["journal"])
            packet=json.loads(path.read_text())
            packet["body"]["state"]["payload"]=99
            path.write_text(json.dumps(packet))
            with self.assertRaises(ValueError): load(path,self.key)
            with self.assertRaises(FileExistsError): supervise(self.root,self.devices,[CAP],self.key,d)
    def test_invalid_grant(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): supervise(self.root,self.devices,[],self.key,d)
