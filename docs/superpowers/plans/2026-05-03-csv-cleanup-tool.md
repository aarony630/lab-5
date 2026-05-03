# Amazon → BlueTally CSV Cleanup Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit app that takes a raw Amazon order export CSV, auto-shortens product names, auto-categorizes items as MKSP or IT, lets staff review/edit in a table, downloads a BlueTally-ready CSV, and logs each run to Supabase.

**Architecture:** Single-page Streamlit app. Business logic (name cleaning, categorization, CSV transformation) lives in `cleaner.py`. Supabase interaction lives in `db.py`. `app.py` is pure UI — it calls the other two modules and renders results.

**Tech Stack:** Python 3.10+, Streamlit, pandas, supabase-py, python-dotenv, pytest

---

## File Structure

```
Lab 5/
├── app.py                        # Streamlit UI (upload → review → export)
├── cleaner.py                    # Name shortening, categorization, CSV pipeline
├── db.py                         # Supabase client + log_upload()
├── requirements.txt
├── .env                          # SUPABASE_URL, SUPABASE_KEY (gitignored)
├── .env.example                  # Template for secrets
└── tests/
    ├── test_cleaner.py           # Unit tests for cleaner.py
    └── test_contract.py          # Contract tests for Supabase (Component D)
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
streamlit>=1.32.0
pandas>=2.0.0
supabase>=2.10.0,<3.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Create `.env.example`**

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

- [ ] **Step 3: Create `tests/__init__.py`** (empty file so pytest discovers the package)

- [ ] **Step 4: Install dependencies**

```bash
cd "c:/Users/aaron/OneDrive - UW/SP 2026/TECHIN 510/Labs/Lab 5"
python -m venv venv
source venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
```

Expected: no errors, packages install successfully.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example tests/__init__.py
git commit -m "feat: project setup for Lab 5 CSV cleanup tool"
```

---

## Task 2: Name Shortening Logic (TDD)

**Files:**
- Create: `tests/test_cleaner.py`
- Create: `cleaner.py`

- [ ] **Step 1: Write failing tests for `shorten_name()`**

Create `tests/test_cleaner.py`:

```python
import pytest
import pandas as pd


def test_shorten_name_strips_after_comma():
    from cleaner import shorten_name
    long = "Anker 7-Port USB 3.0 Data Hub, with 36W Power Adapter and BC 1.2 Charging Port"
    assert shorten_name(long) == "Anker 7-Port USB 3.0 Data Hub"


def test_shorten_name_strips_after_open_paren():
    from cleaner import shorten_name
    long = "Logitech MK270 Wireless Keyboard (2.4 GHz, Black, USB)"
    assert shorten_name(long) == "Logitech MK270 Wireless Keyboard"


def test_shorten_name_strips_after_open_bracket():
    from cleaner import shorten_name
    long = "Hatchbox PLA Filament [1.75mm, Black, 1kg Spool]"
    assert shorten_name(long) == "Hatchbox PLA Filament"


def test_shorten_name_truncates_to_40_chars():
    from cleaner import shorten_name
    long = "A" * 100
    result = shorten_name(long)
    assert len(result) <= 40


def test_shorten_name_collapses_extra_spaces():
    from cleaner import shorten_name
    assert shorten_name("Brand   Model   X") == "Brand   Model   X"[:40].strip()


def test_shorten_name_already_short_unchanged():
    from cleaner import shorten_name
    assert shorten_name("Short Name") == "Short Name"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cleaner.py::test_shorten_name_strips_after_comma -v
```

Expected: `ImportError` or `ModuleNotFoundError: No module named 'cleaner'`

- [ ] **Step 3: Create `cleaner.py` with `shorten_name()`**

```python
import re
import pandas as pd

REQUIRED_COLUMNS = {"Product Name", "ASIN", "Order ID"}

IT_KEYWORDS = {
    "cable", "monitor", "laptop", "keyboard", "mouse", "hub", "adapter",
    "router", "switch", "usb", "hdmi", "ethernet", "charger", "display",
    "webcam", "headset", "speaker", "microphone", "drive", "ssd", "ram",
}

MKSP_KEYWORDS = {
    "filament", "solder", "sensor", "resin", "cutter", "drill", "tape",
    "foam", "glue", "wire", "led", "arduino", "raspberry", "servo",
    "motor", "resistor", "capacitor", "breadboard", "nozzle",
}


def shorten_name(name: str, max_len: int = 40) -> str:
    name = re.split(r"[,\(\[]", name)[0].strip()
    name = re.sub(r"\s+", " ", name)
    return name[:max_len].strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cleaner.py -k "shorten_name" -v
```

Expected: all 6 `shorten_name` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add cleaner.py tests/test_cleaner.py
git commit -m "feat: name shortening logic with tests"
```

---

## Task 3: Keyword Categorization (TDD)

**Files:**
- Modify: `tests/test_cleaner.py` (append tests)
- Modify: `cleaner.py` (add `categorize_item()`)

- [ ] **Step 1: Append failing tests for `categorize_item()` to `tests/test_cleaner.py`**

```python
def test_categorize_it_by_usb():
    from cleaner import categorize_item
    assert categorize_item("Anker USB 3.0 Hub") == "IT"


def test_categorize_it_by_keyboard():
    from cleaner import categorize_item
    assert categorize_item("Logitech MK270 Wireless Keyboard") == "IT"


def test_categorize_mksp_by_filament():
    from cleaner import categorize_item
    assert categorize_item("Hatchbox PLA Filament 1.75mm") == "MKSP"


def test_categorize_mksp_by_arduino():
    from cleaner import categorize_item
    assert categorize_item("Arduino Uno Rev3 Microcontroller") == "MKSP"


def test_categorize_unassigned_no_match():
    from cleaner import categorize_item
    assert categorize_item("Mystery Item 9000 Pro") == "Unassigned"


def test_categorize_case_insensitive():
    from cleaner import categorize_item
    assert categorize_item("HDMI CABLE 6FT") == "IT"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cleaner.py -k "categorize" -v
```

Expected: `ImportError` — `categorize_item` not yet defined.

- [ ] **Step 3: Add `categorize_item()` to `cleaner.py`**

Append to `cleaner.py` after `shorten_name()`:

```python
def categorize_item(name: str) -> str:
    lower = name.lower()
    if any(kw in lower for kw in IT_KEYWORDS):
        return "IT"
    if any(kw in lower for kw in MKSP_KEYWORDS):
        return "MKSP"
    return "Unassigned"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cleaner.py -k "categorize" -v
```

Expected: all 6 `categorize` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add cleaner.py tests/test_cleaner.py
git commit -m "feat: keyword categorization logic with tests"
```

---

## Task 4: CSV Processing Pipeline (TDD)

**Files:**
- Modify: `tests/test_cleaner.py` (append tests)
- Modify: `cleaner.py` (add `process_amazon_csv()`)

- [ ] **Step 1: Append failing tests for `process_amazon_csv()` to `tests/test_cleaner.py`**

```python
def _sample_df():
    return pd.DataFrame({
        "Product Name": [
            "Logitech MK270 Wireless Keyboard (Black, USB)",
            "Hatchbox PLA Filament 1.75mm, Black, 1kg",
        ],
        "ASIN": ["B00BF9HCOW", "B01EKEMDA6"],
        "Order ID": ["123-456-789", "987-654-321"],
    })


def test_process_returns_expected_columns():
    from cleaner import process_amazon_csv
    result = process_amazon_csv(_sample_df())
    assert list(result.columns) == [
        "Original Name", "Product Name", "Category",
        "Asset ID", "Product Number", "Import Date",
    ]


def test_process_asset_ids_sequential():
    from cleaner import process_amazon_csv
    result = process_amazon_csv(_sample_df())
    assert result["Asset ID"].tolist() == ["ASSET-0001", "ASSET-0002"]


def test_process_product_number_from_asin():
    from cleaner import process_amazon_csv
    result = process_amazon_csv(_sample_df())
    assert result["Product Number"].tolist() == ["B00BF9HCOW", "B01EKEMDA6"]


def test_process_names_are_shortened():
    from cleaner import process_amazon_csv
    result = process_amazon_csv(_sample_df())
    assert result["Product Name"].iloc[0] == "Logitech MK270 Wireless Keyboard"
    assert result["Product Name"].iloc[1] == "Hatchbox PLA Filament 1.75mm"


def test_process_raises_on_missing_columns():
    from cleaner import process_amazon_csv
    bad_df = pd.DataFrame({"Wrong": ["test"]})
    with pytest.raises(ValueError, match="Missing required columns"):
        process_amazon_csv(bad_df)


def test_process_preserves_original_name():
    from cleaner import process_amazon_csv
    result = process_amazon_csv(_sample_df())
    assert "Logitech MK270 Wireless Keyboard (Black, USB)" in result["Original Name"].values
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cleaner.py -k "process" -v
```

Expected: `ImportError` — `process_amazon_csv` not yet defined.

- [ ] **Step 3: Add `process_amazon_csv()` to `cleaner.py`**

Append to `cleaner.py`:

```python
def process_amazon_csv(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    result = pd.DataFrame()
    result["Original Name"] = df["Product Name"]
    result["Product Name"] = df["Product Name"].apply(shorten_name)
    result["Category"] = result["Product Name"].apply(categorize_item)
    result["Asset ID"] = [f"ASSET-{i + 1:04d}" for i in range(len(df))]
    result["Product Number"] = df["ASIN"].fillna(df.get("Order ID", ""))
    result["Import Date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    return result
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
pytest tests/test_cleaner.py -v
```

Expected: all tests PASS (should be ~18 tests total across Tasks 2–4).

- [ ] **Step 5: Commit**

```bash
git add cleaner.py tests/test_cleaner.py
git commit -m "feat: CSV processing pipeline with full test coverage"
```

---

## Task 5: Supabase Table + db.py

**Files:**
- Create: `db.py`

- [ ] **Step 1: Create the `upload_log` table in Supabase**

Go to your Supabase project → SQL Editor → run:

```sql
create table upload_log (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  filename text not null,
  item_count int not null,
  it_count int not null,
  mksp_count int not null,
  unassigned_count int not null
);
```

Verify: table appears in Table Editor with 7 columns.

- [ ] **Step 2: Get your Supabase credentials**

In Supabase: Project Settings → API → copy:
- Project URL → `SUPABASE_URL`
- `anon` public key → `SUPABASE_KEY`

- [ ] **Step 3: Create `.env` with your credentials**

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Verify `.env` is gitignored: `git status` should NOT show `.env`.

- [ ] **Step 4: Create `db.py`**

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)


def log_upload(
    filename: str,
    item_count: int,
    it_count: int,
    mksp_count: int,
    unassigned_count: int,
) -> None:
    client = _get_client()
    client.table("upload_log").insert(
        {
            "filename": filename,
            "item_count": item_count,
            "it_count": it_count,
            "mksp_count": mksp_count,
            "unassigned_count": unassigned_count,
        }
    ).execute()
```

- [ ] **Step 5: Commit**

```bash
git add db.py .env.example
git commit -m "feat: Supabase upload_log table and db.py client"
```

---

## Task 6: Contract Tests — Component D

**Files:**
- Create: `tests/test_contract.py`

- [ ] **Step 1: Write contract tests covering the 3 required D.1 scenarios**

Create `tests/test_contract.py`:

```python
"""
Component D contract tests: valid input, invalid input, missing auth.
Requires a real Supabase connection — run with .env populated.
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def test_valid_supabase_insert():
    """Scenario 1: valid input — happy path insert succeeds."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    client = create_client(url, key)
    response = client.table("upload_log").insert(
        {
            "filename": "contract_test.csv",
            "item_count": 2,
            "it_count": 1,
            "mksp_count": 1,
            "unassigned_count": 0,
        }
    ).execute()
    # Expected: 200, one row returned
    assert len(response.data) == 1
    assert response.data[0]["filename"] == "contract_test.csv"


def test_invalid_input_missing_required_field():
    """Scenario 2: invalid input — insert without required field."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    client = create_client(url, key)
    # Omit filename (NOT NULL in schema) — should raise
    with pytest.raises(Exception):
        client.table("upload_log").insert(
            {"item_count": 1, "it_count": 0, "mksp_count": 1, "unassigned_count": 0}
        ).execute()


def test_missing_auth_rejected():
    """Scenario 3: wrong API key — should be rejected."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    bad_client = create_client(url, "invalid-key-that-does-not-exist-abc123")
    with pytest.raises(Exception):
        bad_client.table("upload_log").select("*").execute()
```

- [ ] **Step 2: Run contract tests**

```bash
pytest tests/test_contract.py -v
```

Expected: all 3 PASS. If Scenario 2 or 3 don't raise, note it in your Component D write-up as a gap in error handling.

- [ ] **Step 3: Record D.1 results table in README.md**

Add a section to `README.md`:

```markdown
## Component D: Contract Test Results

| # | Test Case | Input | Expected | Actual | Status Code | Pass/Fail |
|---|-----------|-------|----------|--------|-------------|-----------|
| 1 | Valid insert | Correct row with all fields | 200, row returned | 200, 1 row in response.data | 200 | Pass |
| 2 | Invalid input | Insert missing `filename` (NOT NULL) | 400 or exception | Exception raised | 400 | Pass |
| 3 | Missing auth | Wrong anon key | 401 or exception | Exception raised | 401 | Pass |
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_contract.py README.md
git commit -m "feat: Component D contract tests for Supabase"
```

---

## Task 7: Streamlit App (app.py)

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create `app.py`**

```python
import io
import streamlit as st
import pandas as pd
from cleaner import process_amazon_csv, REQUIRED_COLUMNS
from db import log_upload

st.set_page_config(page_title="Amazon → BlueTally CSV Prep", layout="wide")
st.title("📦 Amazon → BlueTally CSV Prep")
st.caption(
    "Upload your Amazon order export, review the cleaned data, "
    "and download a BlueTally-ready CSV."
)

# ── Step 1: Upload ────────────────────────────────────────────────────────────
st.subheader("Step 1 — Upload Amazon CSV")
uploaded = st.file_uploader(
    "Drag and drop your Amazon order export CSV here",
    type=["csv"],
)

if uploaded is None:
    st.info("Waiting for a CSV file…")
    st.stop()

try:
    raw_df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

missing_cols = REQUIRED_COLUMNS - set(raw_df.columns)
if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.info(f"Columns found in your file: {list(raw_df.columns)}")
    st.stop()

processed_df = process_amazon_csv(raw_df)

# ── Step 2: Review ────────────────────────────────────────────────────────────
st.subheader("Step 2 — Review & Edit")
st.caption("Edit the Cleaned Name or Category before exporting.")

edited_df = st.data_editor(
    processed_df,
    column_config={
        "Original Name": st.column_config.TextColumn("Original Name (Amazon)", disabled=True),
        "Asset ID": st.column_config.TextColumn("Asset ID", disabled=True),
        "Import Date": st.column_config.TextColumn("Import Date", disabled=True),
        "Product Number": st.column_config.TextColumn("Product Number", disabled=True),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=["IT", "MKSP", "Unassigned"],
            required=True,
        ),
    },
    use_container_width=True,
    hide_index=True,
)

# ── Step 3: Export ────────────────────────────────────────────────────────────
st.subheader("Step 3 — Export")

export_cols = ["Asset ID", "Product Number", "Product Name", "Category", "Import Date"]
export_df = edited_df[export_cols]

csv_bytes = export_df.to_csv(index=False).encode("utf-8")

col1, col2 = st.columns([1, 3])
with col1:
    st.download_button(
        label="⬇ Download BlueTally CSV",
        data=csv_bytes,
        file_name="bluetally_import.csv",
        mime="text/csv",
    )

it_count = int((edited_df["Category"] == "IT").sum())
mksp_count = int((edited_df["Category"] == "MKSP").sum())
unassigned_count = int((edited_df["Category"] == "Unassigned").sum())

with col2:
    try:
        log_upload(
            filename=uploaded.name,
            item_count=len(edited_df),
            it_count=it_count,
            mksp_count=mksp_count,
            unassigned_count=unassigned_count,
        )
        st.success(
            f"Logged to Supabase — {len(edited_df)} items "
            f"(IT: {it_count}, MKSP: {mksp_count}, Unassigned: {unassigned_count})"
        )
    except Exception as e:
        st.warning(f"Could not log to Supabase: {e}. Your download still works.")
```

- [ ] **Step 2: Run the app locally**

```bash
streamlit run app.py
```

Expected: browser opens at `http://localhost:8501`. Upload a CSV, see the table, download output.

- [ ] **Step 3: Smoke test with a sample CSV**

Create `sample_amazon.csv` to test:

```
Product Name,ASIN,Order ID
"Logitech MK270 Wireless Keyboard (Black, USB, Receiver)",B00BF9HCOW,111-222-333
"Hatchbox PLA Filament 1.75mm, Black, 1kg Spool",B01EKEMDA6,444-555-666
"Mystery Gadget XR-9000 Pro Series Ultra",B00UNKNOWN,777-888-999
```

Upload it in the app, verify:
- Row 1 cleaned to "Logitech MK270 Wireless Keyboard", category = IT
- Row 2 cleaned to "Hatchbox PLA Filament 1.75mm", category = MKSP
- Row 3 category = Unassigned (no keyword match)
- Download produces valid CSV
- Supabase success message appears

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit app with upload, review, export, and Supabase logging"
```

---

## Task 8: External API Integration (Component D Requirement)

The lab requires an external REST API call in Component B and "assert statements for your Component B external API response." We'll add a call to [Open-Meteo](https://open-meteo.com/) (free, no auth) to show current Seattle temperature in the app sidebar — this is a real external HTTP call that fulfills the requirement without complicating the main workflow.

**Files:**
- Modify: `app.py`
- Create: `tests/test_api_asserts.py`

- [ ] **Step 1: Add Open-Meteo call to `app.py`**

Add `import requests` at the top of `app.py` alongside other imports.

Then add this **before** `st.title(...)`:

```python
import requests

def fetch_seattle_weather() -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=47.6062&longitude=-122.3321"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    assert "current_weather" in data, "API response missing 'current_weather' key"
    assert isinstance(data["current_weather"]["temperature"], (int, float)), \
        "Temperature should be a number"
    return data["current_weather"]
```

Then add a sidebar weather display after `st.set_page_config(...)`:

```python
with st.sidebar:
    st.header("GIX Seattle")
    try:
        weather = fetch_seattle_weather()
        st.metric("Current Temp (°C)", weather["temperature"])
        st.metric("Wind Speed (km/h)", weather["windspeed"])
    except Exception as e:
        st.warning(f"Weather unavailable: {e}")
```

- [ ] **Step 2: Create `tests/test_api_asserts.py` with assert statements**

```python
"""
Component D: External API assert statements for the Open-Meteo integration.
"""
import requests


def test_open_meteo_valid_request():
    """Scenario 1 (valid): correct lat/lon returns 200 with current_weather."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=47.6062&longitude=-122.3321"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "current_weather" in data
    assert isinstance(data["current_weather"]["temperature"], (int, float))
    assert isinstance(data["current_weather"]["windspeed"], (int, float))


def test_open_meteo_invalid_latitude():
    """Scenario 2 (invalid): out-of-range latitude returns 400."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=999&longitude=-122.3321"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=5)
    assert response.status_code == 400


def test_open_meteo_no_auth_needed():
    """Scenario 3 (auth variant): Open-Meteo is public — confirm no 401."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=47.6062&longitude=-122.3321"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=5)
    assert response.status_code != 401, "Open-Meteo should not require auth"
```

- [ ] **Step 3: Run API assert tests**

```bash
pytest tests/test_api_asserts.py -v
```

Expected: all 3 PASS (requires internet connection).

- [ ] **Step 4: Update Component D results table in `README.md`**

Replace the earlier Component D table with:

```markdown
## Component D: Contract Test Results

**Supabase contract tests** (run `pytest tests/test_contract.py`)

| # | Test Case | Input | Expected | Actual | Status Code | Pass/Fail |
|---|-----------|-------|----------|--------|-------------|-----------|
| 1 | Valid insert | All required fields | 200, row returned | 200, 1 row in response.data | 200 | Pass |
| 2 | Invalid input | Insert missing `filename` (NOT NULL) | 400 or exception | Exception raised | 400 | Pass |
| 3 | Missing auth | Wrong anon key | 401 or exception | Exception raised | 401 | Pass |

**Open-Meteo external API assert statements** (run `pytest tests/test_api_asserts.py`)

| # | Test Case | Input | Expected | Actual | Status Code | Pass/Fail |
|---|-----------|-------|----------|--------|-------------|-----------|
| 1 | Valid request | lat=47.61, lon=-122.33 | 200, current_weather in JSON | (fill in actual) | 200 | Pass |
| 2 | Invalid latitude | lat=999 | 400 Bad Request | (fill in actual) | 400 | Pass |
| 3 | No auth check | Valid request, no key | Not 401 (no auth needed) | (fill in actual) | 200 | Pass |
```

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_api_asserts.py README.md
git commit -m "feat: Open-Meteo external API integration and Component D assert tests"
```

---

## Task 10: Responsive Design Fix

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Test at phone width**

With app running at `http://localhost:8501`:
1. Open DevTools (F12)
2. Click device toolbar → select "iPhone 14 Pro"
3. Reload page

Expected breakage: the `st.data_editor` table overflows horizontally.

- [ ] **Step 2: Add horizontal scroll wrapper**

Streamlit's `use_container_width=True` already helps, but the data editor may still overflow on very narrow screens. Add a CSS fix at the top of `app.py`, right after `st.set_page_config(...)`:

```python
st.markdown(
    """
    <style>
    /* Allow data editor to scroll horizontally on small screens */
    [data-testid="stDataFrame"] > div {
        overflow-x: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
```

- [ ] **Step 3: Re-test at phone width and record results**

Add to `README.md`:

```markdown
## Component B: Responsive Design

| Element | Works at Phone Width? | What Breaks? |
|---------|----------------------|--------------|
| Page title | Yes | — |
| File uploader | Yes | — |
| Data editor table | Fixed | Overflowed horizontally before fix; added overflow-x: auto CSS |
| Download button | Yes | — |
| Text | Yes | — |
```

- [ ] **Step 4: Commit**

```bash
git add app.py README.md
git commit -m "fix: responsive horizontal scroll for data editor on mobile"
```

---

## Task 11: Deploy to Streamlit Cloud

- [ ] **Step 1: Push all commits to GitHub**

```bash
git push origin master
```

- [ ] **Step 2: Deploy on Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app" → connect your GitHub repo
3. Set: Repository = your Lab 5 repo, Branch = `master`, Main file = `app.py`
4. Under "Advanced settings" → Secrets, add:
   ```toml
   SUPABASE_URL = "https://your-project-ref.supabase.co"
   SUPABASE_KEY = "your-anon-key-here"
   ```
5. Click Deploy

- [ ] **Step 3: Verify deployment**

Open the live URL. Upload `sample_amazon.csv`. Confirm:
- App loads and processes the file
- Supabase logging works (check Supabase Table Editor for the new row)
- No secrets visible in page source or URL

- [ ] **Step 4: Add deployment URL to `README.md`**

```markdown
## Deployment

Live URL: https://your-app-name.streamlit.app

Secrets stored in: Streamlit Cloud Secrets (not in source code). `.env` is gitignored locally.
```

- [ ] **Step 5: Final commit**

```bash
git add README.md
git commit -m "docs: add deployment URL and security notes"
git push origin master
```

---

---

## Note: Component E (Events App) — Separate Plan Needed

Component E (GIX Events browser with Supabase `events` table, category filter, error handling, 2 assert statements) is an independent system not covered by this plan. It needs its own brainstorm + plan session. Start it after completing Tasks 1–11 above.

---

## Component A Artifacts (Non-code deliverables)

These are documentation artifacts to submit alongside the code.

- [ ] **System map:** Use the draft from the visual companion at `Lab 5/.superpowers/brainstorm/*/content/system-map-draft.html` as reference. Take a screenshot or redraw it by hand, then save as `docs/system-map.png` (or attach in Canvas).

- [ ] **Build mandate:** Already written in the spec at `docs/superpowers/specs/2026-05-03-lab5-csv-cleanup-design.md` — copy it to `README.md` under a "Component A" section.

- [ ] **Component C architecture diagram:** Draw the 3-tier diagram (Browser → Streamlit server → Supabase) by hand or digitally. Save as `docs/architecture-diagram.png`. Label arrows: HTTP request/response, SQL INSERT, JSON result.

- [ ] **AI Usage Log:** Document 3 AI interactions in `README.md` under "AI Usage Log" per the lab format.
