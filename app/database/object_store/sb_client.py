import os
from dotenv import load_dotenv
from supabase import Client, create_client
from app.core.config import settings


SUPABASE_URL =settings.SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
BUCKET_NAME = settings.SUPABASE_BUCKET_NAME

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "Missing Supabase credentials. Ensure 'SUPABASE_URL' and "
        "'SUPABASE_SERVICE_ROLE_KEY' are defined in your .env file."
    )

# Instantiate the single shared client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)