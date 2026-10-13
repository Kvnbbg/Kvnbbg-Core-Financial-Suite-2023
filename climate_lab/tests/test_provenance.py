"""Tests for provenance metadata and local snapshot integrity."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from provenance import ProvenanceError, validate_manifest


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.snapshot = Path(self.temp.name) / "snapshot.csv"
        self.snapshot.write_text("year,value\n2020,1.2\n", encoding="utf-8")
        self.manifest = {
            "dataset_id": "example-series-001",
            "source_url": "https://example.org/data.csv",
            "retrieved_at": "2026-10-12T10:00:00Z",
            "dataset_version": "release-1",
            "license": "review-required",
            "units": "index points",
            "geography": "example-region",
            "variable": "example-index",
            "sha256": hashlib.sha256(self.snapshot.read_bytes()).hexdigest(),
        }

    def test_valid_manifest_checks_snapshot_digest(self):
        result = validate_manifest(self.manifest, self.snapshot)
        self.assertEqual(result["validation"], "sha256_match")
        self.assertEqual(result["sha256"], self.manifest["sha256"])

    def test_missing_metadata_is_rejected(self):
        with self.assertRaisesRegex(ProvenanceError, "manquants"):
            validate_manifest({"dataset_id": "incomplete"}, self.snapshot)

    def test_non_https_source_is_rejected(self):
        self.manifest["source_url"] = "http://example.org/data.csv"
        with self.assertRaises(ProvenanceError):
            validate_manifest(self.manifest, self.snapshot)

    def test_timestamp_must_include_timezone(self):
        self.manifest["retrieved_at"] = "2026-10-12T10:00:00"
        with self.assertRaises(ProvenanceError):
            validate_manifest(self.manifest, self.snapshot)

    def test_tampered_snapshot_is_rejected(self):
        self.snapshot.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(ProvenanceError, "SHA-256"):
            validate_manifest(self.manifest, self.snapshot)

    def test_missing_snapshot_is_rejected(self):
        with self.assertRaisesRegex(ProvenanceError, "introuvable"):
            validate_manifest(self.manifest, self.snapshot.parent / "missing.csv")


if __name__ == "__main__":
    unittest.main()
