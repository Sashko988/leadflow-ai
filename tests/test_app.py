import json
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class AppTests(unittest.TestCase):
    def test_extract_json_normalizes_values(self):
        value = app.extract_json('prefix {"lead_score": 140, "status": "unknown", "name": ["Ana", "Petrova"]}')
        self.assertEqual(value["lead_score"], 100)
        self.assertEqual(value["status"], "COLD")
        self.assertEqual(value["name"], "Ana, Petrova")

    def test_database_save_and_list(self):
        path = app.config.BASE_DIR / "test_leads.db"
        if path.exists():
            path.unlink()
        lead = {key: None for key in app.FIELDS}
        lead.update({"lead_score": 90, "status": "HOT", "name": "Ana"})
        try:
            with patch.object(app.config, "DATABASE_PATH", path):
                app.init_db()
                lead_id = app.save_lead(lead, "Hello")
                self.assertEqual(lead_id, 1)
                with app.db() as conn:
                    row = conn.execute("SELECT name,status,lead_score FROM leads").fetchone()
                self.assertEqual(tuple(row), ("Ana", "HOT", 90))
        finally:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
