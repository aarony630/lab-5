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

**Deployment URL:** *(add after deploying to Streamlit Cloud)*

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

*(Write 3–5 sentences addressing the transition, system map, and tech stack choice questions from the lab manual)*
