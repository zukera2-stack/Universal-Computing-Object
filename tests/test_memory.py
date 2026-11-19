import unittest
from uco_demo.memory import Memory, Tier, benchmark
from uco_demo.unified import value,add

class MemoryTests(unittest.TestCase):
    def test_integrity_and_capacity(self):
        for policy in ("adaptive","lru"):
            m=Memory(policy)
            obj=add(value(2),value(3))
            k=m.put(obj,2,5)
            obj["children"][0]["payload"]=99
            keys=[m.put(value(i),2,20) for i in range(12)]
            for key in [k]+keys*10:
                result=m.get(key)
                if key==k: self.assertEqual(result,add(value(2),value(3)))
                self.assertTrue(all(m.used(i)<=t.capacity for i,t in enumerate(m.tiers)))
            self.assertGreater(m.metrics()["moves"],0)
    def test_oversize_and_missing(self):
        m=Memory()
        with self.assertRaises(ValueError): m.put(value(1),65,1)
        with self.assertRaises(ValueError): m.get("missing")
        m.put(value(1),64,1)
        with self.assertRaises(ValueError): m.put(value(2),1,1)
    def test_determinism_and_accounting(self):
        a=benchmark()
        self.assertEqual(a,benchmark())
        for case in a.values():
            for m in case.values():
                self.assertEqual(m["total"],m["access"]+m["movement"]+m["storage"])
    def test_cold_scan_resistance(self):
        a=benchmark()["scan"]
        self.assertLessEqual(a["adaptive"]["moves"],a["lru"]["moves"])
    def test_invalid_input(self):
        m=Memory()
        for args in ((True,1),(1,False),(0,1)):
            with self.assertRaises(ValueError): m.put(value(1),*args)
        with self.assertRaises(ValueError): Memory("bad")
        with self.assertRaises(ValueError): Memory(tiers=(Tier(0,1,1),)*3)
