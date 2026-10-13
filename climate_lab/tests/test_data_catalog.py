"""Tests for the centralized source catalog and its explicit data status."""
import json
import unittest
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data_catalog.json"


class DataCatalogTests(unittest.TestCase):
    def test_catalog_is_valid_and_explicitly_not_imported(self):
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], 1)
        self.assertEqual(catalog["status"], "catalog_only_no_external_data_downloaded")
        self.assertGreaterEqual(len(catalog["sources"]), 4)

    def test_sources_have_https_urls_and_research_checks(self):
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        identifiers = set()
        for source in catalog["sources"]:
            with self.subTest(source=source.get("id")):
                self.assertTrue(source["id"])
                self.assertNotIn(source["id"], identifiers)
                identifiers.add(source["id"])
                self.assertTrue(source["url"].startswith("https://"))
                self.assertTrue(source["organization"])
                self.assertTrue(source["intended_use"])
                self.assertEqual(source["data_status"], "official_source_link_only")
                self.assertTrue(source["checks"])


if __name__ == "__main__":
    unittest.main()
