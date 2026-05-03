---
name: Lab 5 — Amazon → BlueTally CSV Cleanup Tool
description: Streamlit app that takes raw Amazon order CSVs, cleans product names, auto-categorizes items as MKSP or IT, and exports a BlueTally-ready CSV. Includes Supabase upload log.
type: project
---

# Lab 5 Design: Amazon → BlueTally CSV Prep Tool

## Component A: Interview Synthesis

### Interviewee
**Maason Kao** — manages equipment checkout/return at GIX (with Kevin)

### Workflow (as-is)
1. Amazon purchases arrive → staff set up table on 3rd floor
2. Staff maintain a **listing spreadsheet** of team-purchased items
3. Students return items → staff mark on spreadsheet and add barcode
4. Kevin + Maason manually sort each item: **MKSP** or **IT**
5. Staff import to **BlueTally** (inventory system) via CSV upload
6. For checkout: student checks in with **Purchase Team first**, then checks in/out via **BlueTally**

### Pain Points
- **Volume:** Too many items to manually sort (does not scale)
- **Product names:** Amazon descriptions are too long for BlueTally — must be manually shortened
- **CSV friction:** Manually-filled spreadsheet → BlueTally upload has friction; some fields must be added manually after import
- **Two-step check-in:** Students must visit two touchpoints (Purchase Team + BlueTally) to check out equipment

### System Touchpoints

**Touchpoint 1 — Staff receiving items**
- **Who:** Kevin / Maason (operations staff)
- **What:** Marking items on spreadsheet, adding barcodes, sorting to MKSP or IT
- **Device:** Desktop at their desk (3rd floor table area)

**Touchpoint 2 — BlueTally CSV import**
- **Who:** Maason (operations staff)
- **What:** Exporting spreadsheet as CSV, cleaning product names manually, uploading to BlueTally
- **Device:** Desktop

### Build Mandate
> "Based on the interview, I will build a **CSV cleanup and categorization tool** because the interviewee said Amazon product names are too long and items must be manually sorted to MKSP or IT, which means the design must automate name shortening and keyword-based categorization before export to BlueTally."

---

## Component B: App Design

### Tech Stack
**Streamlit + Python + Supabase**

**Justification:** The tool serves 2 internal staff users with no authentication requirement and its primary job is processing a CSV file — Streamlit is the right tool; Next.js would add complexity without benefit.

### App: Amazon → BlueTally CSV Prep

#### User Flow (3 steps)
1. **Upload** — Staff uploads raw Amazon order export CSV via drag-and-drop
2. **Review** — App displays a `st.data_editor` table with:
   - Original Amazon product name (read-only, dimmed)
   - Auto-cleaned product name (editable text column)
   - Auto-assigned category (MKSP / IT / Unassigned, editable selectbox column)
   - Auto-generated Asset ID (read-only)
3. **Export** — Download BlueTally-ready CSV; run is logged to Supabase automatically

#### Name Shortening Logic
- Strip everything after the first comma, dash, or open bracket/parenthesis
- Truncate to 40 characters max
- Keep: Brand + Model (first 2–3 meaningful tokens)

#### Categorization Keywords
| Category | Keywords |
|----------|----------|
| IT | cable, monitor, laptop, keyboard, mouse, hub, adapter, router, switch, usb, hdmi, ethernet, charger |
| MKSP | filament, solder, sensor, resin, cutter, drill, tape, foam, glue, wire, led, arduino, raspberry, servo |
| Unassigned | anything that doesn't match — staff must pick manually |

#### BlueTally Output CSV Fields
| Field | Source |
|-------|--------|
| Asset ID | Auto-generated (`ASSET-0001` … `ASSET-NNNN`, sequential within each upload batch) |
| Product Number | Mapped from Amazon's `ASIN` column (fallback: `Order ID`) |
| Product Name | Cleaned name |
| Category | MKSP or IT |
| Import Date | Today's date |

#### Supabase Schema

**Table: `upload_log`**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| created_at | timestamptz | Auto |
| filename | text | Uploaded filename |
| item_count | int | Total rows processed |
| it_count | int | Rows assigned to IT |
| mksp_count | int | Rows assigned to MKSP |
| unassigned_count | int | Rows without auto-category |

#### Error Handling
- Wrong file type (not CSV): show `st.error()` before processing
- Missing expected Amazon columns (`Product Name`, `ASIN`, `Order ID`): show which columns were found vs. expected and abort processing
- Supabase insert fails: show warning but still allow CSV download (log failure is non-blocking)

#### Security
- Supabase URL + key in `.env` (loaded via `python-dotenv`)
- `.env` in `.gitignore`

### Responsive Design
- Primary users are desktop staff; phone width is not a core requirement
- Still check at iPhone width and fix the most critical breakage (likely the preview table — add horizontal scroll)

### Deployment
- Deploy to **Streamlit Cloud**
- Confirm no secrets exposed in deployed environment (use Streamlit Secrets for env vars)
