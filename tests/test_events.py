"""
Component E: assert statements and error scenario tests for events/Supabase pipeline.
Requires .env with real Supabase credentials.
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def _client():
    from supabase import create_client
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def test_events_returns_list():
    """Assert 1: query returns a list."""
    response = _client().table("events").select("*").execute()
    assert isinstance(response.data, list)


def test_events_have_required_fields():
    """Assert 2: every event has title and category."""
    response = _client().table("events").select("*").execute()
    assert len(response.data) > 0
    for event in response.data:
        assert "title" in event
        assert "category" in event


def test_category_filter_works():
    """Error scenario 1: filter returns only matching category."""
    response = _client().table("events").select("*").eq("category", "Workshop").execute()
    assert all(e["category"] == "Workshop" for e in response.data)


def test_empty_category_returns_empty():
    """Error scenario 2: filter on nonexistent category returns empty list, not error."""
    response = _client().table("events").select("*").eq("category", "DoesNotExist").execute()
    assert isinstance(response.data, list)
    assert len(response.data) == 0


def test_missing_credentials_raises():
    """Error scenario 3: missing credentials raises before hitting Supabase."""
    with pytest.raises(Exception):
        from supabase import create_client
        client = create_client("https://fake.supabase.co", "fake-key")
        client.table("events").select("*").execute()
