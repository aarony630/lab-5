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
    assert len(response.data) == 1
    assert response.data[0]["filename"] == "contract_test.csv"


def test_invalid_input_missing_required_field():
    """Scenario 2: invalid input — insert without required field."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    client = create_client(url, key)
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
