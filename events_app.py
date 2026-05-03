import os
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="GIX Events", layout="wide")
st.title("GIX Events")
st.caption("Browse upcoming GIX events by category.")


@st.cache_data(ttl=300)
def fetch_events(category: str = "All") -> list:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    client = create_client(url, key)
    query = client.table("events").select("*").order("event_date")
    if category != "All":
        query = query.eq("category", category)
    response = query.execute()
    assert isinstance(response.data, list), "Expected list from Supabase"
    assert all("title" in e and "category" in e for e in response.data), \
        "Events missing required fields"
    return response.data


# Category filter
try:
    all_events = fetch_events("All")
except ValueError as e:
    st.error(f"Configuration error: {e}")
    st.stop()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

if not all_events:
    st.info("No events found.")
    st.stop()

categories = ["All"] + sorted(set(e["category"] for e in all_events))
selected = st.selectbox("Filter by category", categories)

try:
    events = fetch_events(selected)
except Exception as e:
    st.error(f"Could not load events: {e}")
    st.stop()

if not events:
    st.info(f"No events in category: {selected}")
else:
    for e in events:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(e["title"])
                st.caption(f"{e.get('event_date', 'TBD')} · {e.get('location', 'TBD')}")
                if e.get("description"):
                    st.write(e["description"])
            with col2:
                st.markdown(f"`{e['category']}`")
