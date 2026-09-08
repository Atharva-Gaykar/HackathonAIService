import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load the environment variables from your .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
# Use the service role key to initialize the client for backend operations
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Error: Missing environment variables in .env file.")
    exit(1)

print("🔄 Initializing Supabase client...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 2. Check the connection by performing a simple, lightweight operation
try:
    # We attempt to list the storage buckets. 
    # Since you are using the service_role key, this will always succeed if keys are valid.
    response = supabase.storage.list_buckets()
    
    print("✅ Successfully connected to Supabase!")
    print(f"📦 Available storage buckets found: {[b.name for b in response]}")

except Exception as e:
    print("❌ Connection Failed! Please check your credentials.")
    print(f"📋 Error Details: {str(e)}")
