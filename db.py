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
