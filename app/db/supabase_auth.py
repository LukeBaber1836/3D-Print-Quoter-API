from supabase import create_client, Client
from app.constants import settings
from functools import lru_cache

@lru_cache()
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client instance.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )