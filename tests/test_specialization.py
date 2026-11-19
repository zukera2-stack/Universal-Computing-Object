import copy
import unittest
from uco_demo import CAP, run
from uco_demo.__main__ import load, pairs

class SpecializationTests(unittest.TestCase):
    def setUp(self):
        self.obj = load("examples/vector_add.json")
        self.a = load("examples/device_scalar.json")
        self.b = load("examples/device_chunked.json")

    def test_equivalence(self):
        original = copy.deepcopy(self.obj)
        x, y = (run(self.obj, d, [CAP]) for d in (self.a, self.b))
        self.assertEqual(x["result"], [5,7,9])
        self.assertEqual(x["result"], y["result"])
        self.assertNotEqual(x["plan"]["strategy"], y["plan"]["strategy"])
        self.assertNotEqual(x["plan"]["plan_hash"], y["plan"]["plan_hash"])
        self.assertEqual(x, run(self.obj, self.a, [CAP]))
        self.assertEqual(original, self.obj)

    def test_chunk_boundary(self):
        self.obj["inputs"] = {"a": list(range(9)), "b": [2]*9}
        self.obj["requirements"]["max_items"] = 9
        for d in (self.a, self.b):
            self.assertEqual(run(self.obj, d, [CAP])["result"], list(range(2,11)))

    def test_missing_grant(self):
        with self.assertRaises(ValueError):
            run(self.obj, self.a, [])

    def test_invalid_objects(self):
        mutations = [
            lambda o: o.update(schema_version="bad"),
            lambda o: o["operation"].update(opcode="bad"),
            lambda o: o["inputs"]["a"].append(1),
            lambda o: o["inputs"]["a"].__setitem__(0, 2**31-1),
            lambda o: o["inputs"]["a"].__setitem__(0, True),
            lambda o: o["requirements"].update(max_items=2),
            lambda o: o.update(code="arbitrary"),
        ]
        for mutate in mutations:
            for d in (self.a, self.b):
                with self.subTest(mutation=mutate, device=d["strategy"]):
                    obj = copy.deepcopy(self.obj)
                    mutate(obj)
                    with self.assertRaises(ValueError):
                        run(obj,d,[CAP])

    def test_invalid_devices(self):
        for change in ({"strategy":"unknown"}, {"max_items":2}, {"capabilities":[]}, {"schema_version":"bad"}, {"code":"arbitrary"}, {"max_items":65537}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                run(self.obj, dict(self.a, **change), [CAP])

    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):
            pairs([("a",1),("a",2)])
