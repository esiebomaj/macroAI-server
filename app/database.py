import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

def get_anon_client() -> Client:
    """Used for auth operations (sign up, sign in) — respects RLS."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_service_client() -> Client:
    """Used for data operations — bypasses RLS only when needed.
    RLS is still the primary security layer since we pass user_id explicitly."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
