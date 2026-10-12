# Climate Finance Research Lab

A dependency-free, reproducible MVP for exploring climate-related portfolio stress. This is a research and education tool, not investment advice or a regulatory capital model.

## Run locally

Requires Python 3.10+; no third-party packages.

```bash
python -m unittest discover -s tests -v
python server.py
```

Open http://127.0.0.1:8000. The server binds to loopback by default. To change the bind address, set `CLIMATE_LAB_HOST`; set `CLIMATE_LAB_PORT` to change the port. Do not expose the development server directly to the public internet.

## What the MVP does

- Serves a browser dashboard and a JSON API.
- Runs deterministic, transparent sector-level portfolio stress scenarios.
- Reports estimated portfolio loss, loss percentage, sector contributions, and scenario assumptions.
- Rejects unknown sectors, negative/non-finite exposure values, and malformed requests.
- Uses no third-party dependencies, external calls, credentials, or real customer data.

## Scientific status and interpretation

The scenario shock coefficients in `server.py` are **illustrative toy parameters**, not NGFS outputs, forecasts, calibrated asset-pricing estimates, or official supervisory scenarios. The interface labels results accordingly. They are intended to exercise the workflow and make assumptions visible; do not use them to make investment, credit, insurance, or regulatory decisions.

The next research step is to build a versioned ingestion pipeline for downloaded NGFS / World Bank / ECB data, preserve source files and metadata, map variables to sectors and horizons, document transformations, and replace toy coefficients only after review and validation. Do not scrape or silently substitute data.

## Data sources to integrate (verify version, license, units, geography and horizon)

- NGFS scenarios and technical resources: https://www.ngfs.net/ngfs-scenarios-portal/data-resources/
- NGFS scenario explorer and narratives: https://www.ngfs.net/ngfs-scenarios-portal/explore/
- ECB climate-related indicators and methodology: https://www.ecb.europa.eu/stats/all-key-statistics/horizontal-indicators/sustainability-indicators/html/index.en.html
- World Bank Climate Change Knowledge Portal data/API: https://climateknowledgeportal.worldbank.org/index.php/download-data
- Copernicus Climate Data Store API: https://cds.climate.copernicus.eu/en/how-to-api

NGFS scenarios are conditional pathways, not probability-weighted predictions. ECB notes that carbon-emission and physical-risk indicators are analytical and have methodological/data limitations; treat them with care.

## API

- `GET /api/health`
- `GET /api/scenarios`
- `GET /api/data-sources` — centralized source catalog; links only, no automatic download
- `POST /api/simulate` with JSON:
  ```json
  {
    "scenario": "orderly_transition",
    "horizon_years": 10,
    "portfolio": [
      {"sector": "energy", "value": 100000, "emissions_intensity": 0.8},
      {"sector": "technology", "value": 50000, "emissions_intensity": 0.1}
    ]
  }
  ```

The emissions intensity is a user-supplied, unitless teaching input in this MVP, not a verified issuer metric. The result is a deterministic sensitivity calculation, not a VaR estimate or a probability of loss.

## Reproducibility and risk controls

- Deterministic calculations; no random seeds or hidden external dependencies.
- Unit tests cover valid inputs, invalid sectors, negative exposures, and scenario availability.
- Keep source snapshots, retrieval date, dataset version, units, geographic coverage, transformation code hash, model version, and configuration for every real-data run.
- For research use, add sensitivity analysis, historical backtesting where defensible, uncertainty intervals, out-of-sample validation, and peer review before interpreting outputs.
- Do not upload confidential portfolios or secrets. Before cloud deployment, add authentication, authorization, rate limiting, request limits, audit logs, TLS, dependency/security scanning, and managed secret storage.

## Methodological alternatives

1. **Top-down scenario repricing:** apply sector or macro shocks; fast and interpretable, but coarse.
2. **Bottom-up issuer mapping:** link issuer emissions, revenue geography and assets to transition/physical hazards; granular but data-intensive.
3. **Econometric panel / local projections:** estimate historical responses; vulnerable to structural breaks and short climate-finance histories.
4. **Integrated assessment model pathways:** use NGFS / IAM variables; coherent narratives, but model and scenario uncertainty remains.
5. **Monte Carlo / Bayesian uncertainty:** useful only when distributions and dependence assumptions are defensible; not automatically more scientific.

## Roadmap

1. MVP and tests (this directory).
2. Data catalog + immutable raw snapshots and provenance manifest.
3. NGFS scenario import with schema/unit validation and version pinning.
4. Sector-to-financial-exposure mapping with explicit coverage and missing-data policy.
5. Comparative models, sensitivity bands, validation report and downloadable run manifest.
6. Deploy behind managed HTTPS/authentication only after security review.


## Provenance gate for real-data research

The dashboard and `GET /api/data-sources` use `data_catalog.json` as the single source catalog. Its status explicitly says that no external dataset has been downloaded or integrated. The catalog provides official entry points and per-source checks; it does not guarantee that a linked dataset is current, licensed for every use, or directly comparable.

Before using a local CSV or other snapshot in an analysis, create a separate JSON manifest with these required string fields:

```json
{
  "dataset_id": "provider-series-or-dataset-id",
  "source_url": "https://official.example/dataset",
  "retrieved_at": "2026-10-12T10:00:00Z",
  "dataset_version": "provider-release-or-version",
  "license": "exact-license-or-review-required",
  "units": "documented units",
  "geography": "documented geography",
  "variable": "provider variable identifier",
  "sha256": "64-character-lowercase-sha256-of-local-snapshot"
}
```

Use `provenance.validate_manifest(manifest, snapshot_path)` to validate required metadata, HTTPS source URL, timezone-aware ISO 8601 retrieval time, and the SHA-256 digest of the local file. It intentionally makes no network requests, does not invent missing metadata, and does not validate the scientific suitability of the data. Keep raw snapshots immutable and store manifests alongside them. A digest proves file identity, not source authenticity or correctness.

Run all tests with:

```bash
python -m unittest discover -s tests -v
```

**Alternative methods:** use a provider-specific downloader only after reviewing its terms and API contract; for high-assurance pipelines, add a signed provenance record and immutable object storage. Do not treat either as a replacement for unit, coverage, and methodological checks.
