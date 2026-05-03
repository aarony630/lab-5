import requests
import streamlit as st
import pandas as pd
from cleaner import process_amazon_csv, REQUIRED_COLUMNS
from db import log_upload

st.set_page_config(page_title="Amazon → BlueTally CSV Prep", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stDataFrame"] > div { overflow-x: auto !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("GIX Seattle")
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=47.6062&longitude=-122.3321&current_weather=true",
            timeout=5,
        )
        resp.raise_for_status()
        weather = resp.json()
        assert "current_weather" in weather
        assert isinstance(weather["current_weather"]["temperature"], (int, float))
        st.metric("Temp (°C)", weather["current_weather"]["temperature"])
        st.metric("Wind (km/h)", weather["current_weather"]["windspeed"])
    except Exception as e:
        st.warning(f"Weather unavailable: {e}")

st.title("📦 Amazon → BlueTally CSV Prep")
st.caption("Upload your Amazon order export, review the cleaned data, and download a BlueTally-ready CSV.")

st.subheader("Step 1 — Upload Amazon CSV")
uploaded = st.file_uploader("Drag and drop your Amazon order export CSV here", type=["csv"])

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
            "Category", options=["IT", "MKSP", "Unassigned"], required=True
        ),
    },
    use_container_width=True,
    hide_index=True,
)

st.subheader("Step 3 — Export")

export_cols = ["Asset ID", "Product Number", "Product Name", "Category", "Import Date"]
csv_bytes = edited_df[export_cols].to_csv(index=False).encode("utf-8")

it_count = int((edited_df["Category"] == "IT").sum())
mksp_count = int((edited_df["Category"] == "MKSP").sum())
unassigned_count = int((edited_df["Category"] == "Unassigned").sum())

col1, col2 = st.columns([1, 3])
with col1:
    st.download_button("⬇ Download BlueTally CSV", data=csv_bytes, file_name="bluetally_import.csv", mime="text/csv")
with col2:
    try:
        log_upload(
            filename=uploaded.name,
            item_count=len(edited_df),
            it_count=it_count,
            mksp_count=mksp_count,
            unassigned_count=unassigned_count,
        )
        st.success(f"Logged to Supabase — {len(edited_df)} items (IT: {it_count}, MKSP: {mksp_count}, Unassigned: {unassigned_count})")
    except Exception as e:
        st.warning(f"Could not log to Supabase: {e}. Your download still works.")
