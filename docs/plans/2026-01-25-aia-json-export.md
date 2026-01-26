# AIA JSON Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Implement a standardized JSON export of current holdings to support integration with the Unified Investment System (V3).

**Architecture:**

- Create a new `src/aia` python package to house the AIA logic, moving away from flat script structure.
- Refactor/Copy holdings parsing logic from `scripts/fetch_market_data.py` to `src/aia/parsers.py` to ensure consistent data access without running the full script.
- Implement `HoldingsExporter` in `src/aia/exporter.py` that conforms to `aia-json-spec.md`.
- exposure a CLI command `aia export-holdings` via `src/aia/cli.py`.

**Tech Stack:** Python 3, Standard Library (json, re, os), Unittest.

---

### Task 1: Initialize Package Structure

**Files:**

- Create: `src/aia/__init__.py` (Empty)
- Create: `src/aia/utils.py` (Logging/Common helpers)

**Step 1: Create directories and init**
Run: `mkdir -p src/aia`
Create empty `src/aia/__init__.py`.

**Step 2: Create utils**
Create `src/aia/utils.py` with basic logging helper (compatible with `fetch_market_data.py`'s `log`).

**Step 3: Verification**
Run: `python3 -c "import src.aia; print('Package init success')"`

---

### Task 2: Implement Holdings Parser

**Files:**

- Create: `src/aia/parsers.py`
- Test: `tests/test_parsers.py`
- Reference: `scripts/fetch_market_data.py`

**Step 1: Write test for parser**
Create `tests/test_parsers.py` with a sample markdown content and assert it parses correctly.

**Step 2: Implement parser**
Port `parse_holdings_md` and `parse_us_holdings_md` logic from `scripts/fetch_market_data.py` to `src/aia/parsers.py`.
Refactor to accept `content` string (dependency injection) to make it testable, with a wrapper that reads the file.

**Step 3: Verification**
Run: `python3 -m unittest tests/test_parsers.py`

---

### Task 3: Implement Holdings Exporter

**Files:**

- Create: `src/aia/exporter.py`
- Test: `tests/test_exporter.py`

**Step 1: Write test for exporter**
Create `tests/test_exporter.py` that mocks the parser data and checks if `holdings_snapshot.json` schema is correct (fields, types, default values).

**Step 2: Implement Exporter**
Implement `HoldingsExporter` class with `export(output_path)` method.

- Ensure `sync_timestamp` is ISO 8601 UTC.
- Map fields correctly (`avg_cost_local`, `market`, etc.).
- Ensure `output` directory creation.

**Step 3: Verification**
Run: `python3 -m unittest tests/test_exporter.py`

---

### Task 4: CLI Implementation

**Files:**

- Create: `src/aia/cli.py`
- Create: `aia` (Shell script in root)

**Step 1: Implement CLI**
Create `src/aia/cli.py` using `argparse`.
Support command: `export-holdings`.
Use `HoldingsExporter`.

**Step 2: Create shell wrapper**
Create `aia` script in root:

```bash
#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m src.aia.cli "$@"
```

Make executable: `chmod +x aia`

**Step 3: Verification**
Run: `./aia export-holdings`
Check if `output/holdings_snapshot.json` is generated.

---

### Verification Plan

### Automated Tests

Run all unit tests:
`python3 -m unittest discover tests`

### Manual Verification

1. Run `./aia export-holdings`
2. Check `output/holdings_snapshot.json` content:
   - Contains `sync_timestamp`
   - Contains `holdings` list
   - Verify sample holding (e.g., AAPL) has `market: "US"`, `currency: "USD"`.
3. Validate against schema requirements in `docs/integration/aia-json-spec.md`.
