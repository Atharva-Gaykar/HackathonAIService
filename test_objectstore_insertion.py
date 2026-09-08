import os
from uuid import uuid4
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")  # set this to your actual bucket name

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not BUCKET_NAME:
    print("❌ Error: Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / SUPABASE_BUCKET_NAME in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---- Test identities (simulating one turn in one thread) ----
user_id = str(uuid4())
thread_id = str(uuid4())
message_id = str(uuid4())

LOCAL_AUDIO_PATH = r"C:\Users\ATHARVA\Downloads\my codes\web\AIService\Audio Samples\Hindi Sample.wav"

with open(LOCAL_AUDIO_PATH, "rb") as f:
    audio_bytes = f.read()
6
# ---- Upload as STT input ----
stt_path = f"{user_id}/stt/{thread_id}/{message_id}.wav"
supabase.storage.from_(BUCKET_NAME).upload(
    stt_path, audio_bytes, file_options={"content-type": "audio/wav"}
)
print(f" STT audio uploaded -> {stt_path}")

# ---- Upload same file as TTS output (simulating the reverse direction for this trial) ----
tts_path = f"{user_id}/tts/{thread_id}/{message_id}.wav"
supabase.storage.from_(BUCKET_NAME).upload(
    tts_path, audio_bytes, file_options={"content-type": "audio/wav"}
)
print(f"TTS audio uploaded -> {tts_path}")

# ---- Verify by listing what landed under this user/thread ----
stt_files = supabase.storage.from_(BUCKET_NAME).list(f"{user_id}/stt/{thread_id}")
tts_files = supabase.storage.from_(BUCKET_NAME).list(f"{user_id}/tts/{thread_id}")
print(f"STT folder contents: {[f['name'] for f in stt_files]}")
print(f"TTS folder contents: {[f['name'] for f in tts_files]}")