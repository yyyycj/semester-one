import unittest
from pathlib import Path
import tempfile

from code.src.storage import JsonStore
from code.src.repositories import Repos
from code.src.services import AccountingService


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = JsonStore(Path(self.tmp.name))
        self.repos = Repos(store)
        self.svc = AccountingService(self.repos)
        self.svc.create_component("C-01", "Capacitor")

    def tearDown(self):
        self.tmp.cleanup()

    def test_negative_stock_not_allowed(self):
        with self.assertRaises(ValueError):
            self.svc.register_movement("ISSUE", [{"component_id": "C-01", "qty": 1}], order_id=None)

    def test_income_then_issue_ok(self):
        self.svc.register_movement("INCOME", [{"component_id": "C-01", "qty": 5}])
        self.svc.register_movement("WRITE_OFF", [{"component_id": "C-01", "qty": 2}])
        bal = self.svc.component_balance()
        self.assertEqual(bal["C-01"], 3)