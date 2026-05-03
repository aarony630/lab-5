# TECHIN 510 — Week 5: Full Stack Development

## Component A: Interview Synthesis

**Interviewee:** Maason Kao — equipment checkout/return at GIX

**Build Mandate:** "Based on the interview, I will build a **CSV cleanup and categorization tool** because the interviewee said Amazon product names are too long and items must be manually sorted to MKSP or IT, which means the design must automate name shortening and keyword-based categorization before export to BlueTally."

**System map:** see `docs/system-map.png` (hand-drawn or screenshot from visual companion)

## Component B: App

**Stack:** Streamlit + Python + Supabase  
**Justification:** 2 internal staff users, no auth needed, primary job is CSV processing — Streamlit fits.

**Supabase schema — table `upload_log`:**  
`id` (uuid), `created_at` (timestamptz), `filename` (text), `item_count` (int), `it_count` (int), `mksp_count` (int), `unassigned_count` (int)

**Responsive Design:**

| Element | Works at Phone Width? | Notes |
|---------|----------------------|-------|
| Page title | Yes | — |
| File uploader | Yes | — |
| Data editor table | Fixed | Added `overflow-x: auto` CSS |
| Download button | Yes | — |
| Text | Yes | — |

**Deployment URL:** https://koxx62ay2xbhrx89ecsyyp.streamlit.app  
**Secrets check:** No secrets in source code — Supabase credentials stored in Streamlit Cloud Secrets, `.env` is gitignored locally.

## Component D: Contract Test Results

Run: `pytest tests/test_contract.py tests/test_api_asserts.py -v`

**Supabase**

| # | Test Case | Input | Expected | Actual | Pass/Fail |
|---|-----------|-------|----------|--------|-----------|
| 1 | Valid insert | All required fields | Row returned | 1 row in response.data | Pass |
| 2 | Invalid input | Missing `filename` (NOT NULL) | Exception | APIError raised | Pass |
| 3 | Missing auth | Wrong anon key | Exception | APIError raised | Pass |

**Open-Meteo external API**

| # | Test Case | Input | Expected | Actual | Pass/Fail |
|---|-----------|-------|----------|--------|-----------|
| 1 | Valid request | lat=47.61, lon=-122.33 | 200 + current_weather | 200, data received | Pass |
| 2 | Invalid latitude | lat=999 | 400 | 400 | Pass |
| 3 | No auth needed | Valid request | Not 401 | 200 | Pass |

## AI Usage Log

*(Document 3 AI interactions per lab format)*

1. **Prompt:** "Help me design the system map for Maason's equipment checkout workflow"  
   **Output:** Visual HTML system map with actors, flow, and pain points  
   **Assumption:** AI assumed BlueTally is the only inventory system  
   **Failure mode:** Could miss secondary tools Maason uses  
   **Fix:** Ask specifically about all tools in use before diagramming

2. **Prompt:** "Build a Streamlit CSV cleanup tool for BlueTally import"  
   **Output:** Full app.py, cleaner.py, db.py with tests  
   **Assumption:** AI assumed Amazon CSV always has `Product Name`, `ASIN`, `Order ID` columns  
   **Failure mode:** Real Amazon exports may use different column names (e.g. `Title`)  
   **Fix:** Prompt with an actual sample CSV so AI sees the real column names

3. **Prompt:** "Write contract tests for the Supabase upload_log table"  
   **Output:** 3 pytest tests for valid insert, invalid input, missing auth  
   **Assumption:** AI assumed RLS would be disabled  
   **Failure mode:** Tests fail with 403 if RLS is on (happened during testing)  
   **Fix:** Include Supabase RLS status in the prompt context

## Reflection

Building in Streamlit was significantly faster than Next.js — a single Python file replaced what would have been pages, API routes, and components across multiple files, which made the iteration loop much tighter. What surprised me most was how much the system map revealed that the interview alone did not: the two-step check-in flow (Purchase Team first, then BlueTally) only became a clear pain point when drawn out as separate touchpoints, because Maason described it casually as "just how it works." The map also made visible that the real bottleneck was not BlueTally itself but the manual transformation step between the Amazon spreadsheet and the import format — a friction point that would have been easy to overlook without mapping the data flow. Streamlit is the right tool when the user is internal staff, there is no authentication requirement, and the primary job is data processing or visualization — exactly this use case. Next.js + Supabase is the right tool when multiple users need to log in, data needs to persist across sessions and users, or the app needs to be a polished public-facing product.
