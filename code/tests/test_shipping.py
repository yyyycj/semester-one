import unittest
from pathlib import Path
import tempfile

from code.src.storage import JsonStore
from code.src.repositories import Repos
from code.src.services import AccountingService


class TestShipping(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = JsonStore(Path(self.tmp.name))
        self.repos = Repos(store)
        self.svc = AccountingService(self.repos)

        self.svc.create_product("P-100", "Device")
        self.svc.create_component("C-01", "Capacitor")
        self.svc.set_bom("P-100", [{"component_id": "C-01", "qty_per_unit": 1}])

        self.oid = self.svc.create_order("P-100", 1)
        self.svc.approve_order(self.oid)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ship_requires_pass(self):
        self.svc.register_unit(self.oid, "S001")
        with self.assertRaises(ValueError):
            self.svc.ship_unit("S001")
        self.svc.record_test("S001", passed=True)
        self.svc.ship_unit("S001")