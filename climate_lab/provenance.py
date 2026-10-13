"""Validation helpers for auditable local research-data snapshots.

This module does not download data or assert that a source is authoritative.
It validates the metadata and SHA-256 digest supplied by the researcher.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REQUIRED_FIELDS = {
    "dataset_id", "source_url", "retrieved_at", "dataset_version",
    "license", "units", "geography", "variable", "sha256",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceError(ValueError):
    """Raised when a local dataset manifest is incomplete or inconsistent."""


def validate_manifest(manifest: Any, snapshot_path: str | Path) -> dict[str, Any]:
    """Validate required provenance fields and verify the snapshot's SHA-256.

    The manifest is expected to describe an already downloaded, local snapshot.
    This function deliberately avoids network calls and never infers missing metadata.
    """
    if not isinstance(manifest, dict):
        raise ProvenanceError("Le manifeste doit être un objet JSON.")
    missing = sorted(REQUIRED_FIELDS - manifest.keys())
    if missing:
        raise ProvenanceError("Champs de provenance manquants : " + ", ".join(missing))
    for field in REQUIRED_FIELDS:
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise ProvenanceError(f"{field} doit être une chaîne non vide.")
    parsed = urlparse(manifest["source_url"])
    if parsed.scheme != "https" or not parsed.netloc:
        raise ProvenanceError("source_url doit être une URL HTTPS absolue.")
    try:
        timestamp = datetime.fromisoformat(manifest["retrieved_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProvenanceError("retrieved_at doit être une date ISO 8601.") from exc
    if timestamp.tzinfo is None:
        raise ProvenanceError("retrieved_at doit inclure un fuseau horaire.")
    expected = manifest["sha256"].lower()
    if not _SHA256.fullmatch(expected):
        raise ProvenanceError("sha256 doit contenir exactement 64 caractères hexadécimaux.")
    path = Path(snapshot_path)
    if not path.is_file():
        raise ProvenanceError("Le snapshot local est introuvable.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ProvenanceError("Le SHA-256 du snapshot ne correspond pas au manifeste.")
    # Return a copy so callers cannot mutate the caller's original dictionary.
    validated = dict(manifest)
    validated["sha256"] = digest
    validated["validation"] = "sha256_match"
    return validated
