import unittest
from pathlib import Path
import tempfile

from code.src.storage import JsonStore
from code.src.repositories import Repos
from code.src.services import AccountingService


class TestOrders(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = JsonStore(Path(self.tmp.name))
        self.repos = Repos(store)
        self.svc = AccountingService(self.repos)

        self.svc.create_product("P-100", "Device")
        self.svc.create_component("C-01", "Capacitor")
        self.svc.set_bom("P-100", [{"component_id": "C-01", "qty_per_unit": 2}])

    def tearDown(self):
        self.tmp.cleanup()

    def test_approve_order_requires_draft(self):
        oid = self.svc.create_order("P-100", 3)
        self.svc.approve_order(oid)
        with self.assertRaises(ValueError):
            self.svc.approve_order(oid)