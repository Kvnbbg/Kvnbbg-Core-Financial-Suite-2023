#!/usr/bin/env python3
"""Dependency-free local server and transparent toy climate stress simulator.

WARNING: coefficients are illustrative teaching assumptions, not empirical estimates,
NGFS data, forecasts, or supervisory capital parameters.
"""
from __future__ import annotations

import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_CATALOG_PATH = ROOT / "data_catalog.json"
HOST = os.environ.get("CLIMATE_LAB_HOST", "127.0.0.1")
PORT = int(os.environ.get("CLIMATE_LAB_PORT", "8000"))

# Illustrative stress coefficients only. Positive values represent loss rates.
# Replace only with versioned, sourced and reviewed estimates in a later research phase.
SECTORS = {
    "energy": {"transition_sensitivity": 0.22, "physical_sensitivity": 0.07},
    "utilities": {"transition_sensitivity": 0.13, "physical_sensitivity": 0.10},
    "transport": {"transition_sensitivity": 0.16, "physical_sensitivity": 0.12},
    "industrials": {"transition_sensitivity": 0.12, "physical_sensitivity": 0.10},
    "agriculture": {"transition_sensitivity": 0.05, "physical_sensitivity": 0.24},
    "real_estate": {"transition_sensitivity": 0.08, "physical_sensitivity": 0.22},
    "technology": {"transition_sensitivity": 0.04, "physical_sensitivity": 0.04},
    "healthcare": {"transition_sensitivity": 0.05, "physical_sensitivity": 0.06},
    "diversified": {"transition_sensitivity": 0.08, "physical_sensitivity": 0.10},
}

SCENARIOS = {
    "orderly_transition": {
        "label": "Transition ordonnée",
        "description": "Transition anticipée et graduelle; sensibilité physique limitée dans ce jouet.",
        "transition_multiplier": 0.65,
        "physical_multiplier": 0.55,
    },
    "disorderly_transition": {
        "label": "Transition désordonnée",
        "description": "Transition tardive et brusque; choc de transition accentué.",
        "transition_multiplier": 1.45,
        "physical_multiplier": 0.75,
    },
    "hot_house_world": {
        "label": "Monde à fortes émissions",
        "description": "Transition faible dans cette hypothèse; risque physique accentué.",
        "transition_multiplier": 0.35,
        "physical_multiplier": 1.65,
    },
}

MAX_BODY_BYTES = 64 * 1024
MAX_POSITIONS = 100
MAX_EXPOSURE = 1_000_000_000_000


class InputError(ValueError):
    """Expected client input validation failure."""


def _finite_number(value: Any, field: str, *, minimum: float = 0.0,
                   maximum: float = MAX_EXPOSURE) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{field} doit être un nombre.")
    number = float(value)
    if not math.isfinite(number) or number < minimum or number > maximum:
        raise InputError(f"{field} doit être compris entre {minimum} et {maximum}.")
    return number


def simulate(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate a deterministic sector stress sensitivity from validated inputs."""
    if not isinstance(payload, dict):
        raise InputError("Le corps JSON doit être un objet.")
    scenario_id = payload.get("scenario", "orderly_transition")
    if scenario_id not in SCENARIOS:
        raise InputError("Scénario inconnu. Consultez GET /api/scenarios.")
    horizon = payload.get("horizon_years", 10)
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon not in (1, 5, 10, 20, 30):
        raise InputError("horizon_years doit être 1, 5, 10, 20 ou 30.")
    positions = payload.get("portfolio")
    if not isinstance(positions, list) or not positions or len(positions) > MAX_POSITIONS:
        raise InputError(f"portfolio doit contenir entre 1 et {MAX_POSITIONS} positions.")
    scenario = SCENARIOS[scenario_id]
    rows = []
    total_value = 0.0
    total_loss = 0.0
    for index, position in enumerate(positions):
        if not isinstance(position, dict):
            raise InputError(f"portfolio[{index}] doit être un objet.")
        sector = position.get("sector")
        if sector not in SECTORS:
            raise InputError(f"Secteur inconnu dans portfolio[{index}].")
        value = _finite_number(position.get("value"), f"portfolio[{index}].value")
        intensity = _finite_number(
            position.get("emissions_intensity", 0.0),
            f"portfolio[{index}].emissions_intensity",
            maximum=2.0,
        )
        sensitivity = SECTORS[sector]
        # Horizon scaling is deliberately linear and explicitly a toy assumption.
        horizon_scale = horizon / 10.0
        transition_rate = sensitivity["transition_sensitivity"] * scenario["transition_multiplier"] * horizon_scale
        # User intensity is a unitless teaching factor; capped to avoid runaway outputs.
        intensity_factor = min(2.0, 0.5 + intensity)
        physical_rate = sensitivity["physical_sensitivity"] * scenario["physical_multiplier"] * horizon_scale
        loss_rate = min(0.95, max(0.0, transition_rate + physical_rate * intensity_factor))
        loss = value * loss_rate
        total_value += value
        total_loss += loss
        rows.append({
            "sector": sector,
            "exposure": round(value, 2),
            "estimated_loss": round(loss, 2),
            "loss_rate_pct": round(loss_rate * 100, 4),
            "transition_component_pct": round(transition_rate * 100, 4),
            "physical_component_pct": round(physical_rate * intensity_factor * 100, 4),
        })
    rows.sort(key=lambda row: row["estimated_loss"], reverse=True)
    return {
        "scenario": scenario_id,
        "scenario_label": scenario["label"],
        "horizon_years": horizon,
        "portfolio_value": round(total_value, 2),
        "estimated_loss": round(total_loss, 2),
        "estimated_loss_pct": round((total_loss / total_value * 100) if total_value else 0.0, 4),
        "positions": rows,
        "method": "deterministic sector sensitivity; illustrative coefficients; no probability model",
        "limitations": [
            "Toy coefficients are not calibrated or sourced from NGFS.",
            "No issuer-level mapping, market repricing, default dynamics, diversification or correlations.",
            "Emissions intensity is a user-entered unitless teaching factor, not verified data.",
            "Linear horizon scaling is an explicit simplification, not a climate projection.",
        ],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ClimateResearchLab/0.1"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: Any) -> None:
        self._send(status, json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path == "/api/health":
            self._json(200, {"status": "ok", "mode": "local research MVP", "external_data": False})
        elif self.path == "/api/data-sources":
            # This is a source catalog, not a claim that remote datasets were imported.
            try:
                catalog = json.loads(DATA_CATALOG_PATH.read_text(encoding="utf-8"))
                self._json(200, catalog)
            except (OSError, json.JSONDecodeError):
                self._json(500, {"error": "Catalogue de sources indisponible ou invalide"})
        elif self.path == "/api/scenarios":
            self._json(200, {
                "scenarios": [{"id": key, **value} for key, value in SCENARIOS.items()],
                "sectors": sorted(SECTORS),
                "warning": "Illustrative toy parameters; not official NGFS values or forecasts.",
            })
        elif self.path in ("/", "/index.html"):
            path = ROOT / "index.html"
            if not path.is_file():
                self._json(404, {"error": "index.html introuvable"})
            else:
                self._send(200, path.read_bytes(), "text/html; charset=utf-8")
        else:
            self._json(404, {"error": "route introuvable"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
        if self.path != "/api/simulate":
            self._json(404, {"error": "route introuvable"})
            return
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            self._json(411, {"error": "Content-Length requis"})
            return
        if length < 1 or length > MAX_BODY_BYTES:
            self._json(413, {"error": f"Corps JSON limité à {MAX_BODY_BYTES} octets"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(200, simulate(payload))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"error": "JSON invalide"})
        except InputError as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        # Avoid logging user-supplied portfolio payloads; retain only standard request logs.
        super().log_message(format, *args)


if __name__ == "__main__":
    print(f"Climate Finance Research Lab: http://{HOST}:{PORT}")
    print("Research MVP only. Do not expose this development server publicly.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
