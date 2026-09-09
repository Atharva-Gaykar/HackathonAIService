from app.stt_model import transcriber
from app.tts_model import tts_generator
from app.database.object_store import supabase_client

BUCKET_NAME = "user-audio-recordings"

USER_ID = "8b56dd78-0eb9-4b1f-b161-856d60c0168c"
THREAD_ID = "2ce7b1c2-8b5f-4b81-b8ae-a1a299d76f30"
INPUT_AUDIO_PATH = f"{USER_ID}/stt/{THREAD_ID}/65ed9212-6166-4f76-baf1-55971b824998.wav"

LOCAL_OUTPUT_PATH = "temp_output.wav"

# ---- Step 1: Fetch input audio from S3 (in memory) ----
audio_bytes = supabase_client.storage.from_(BUCKET_NAME).download(INPUT_AUDIO_PATH)

# ---- Step 2: Transcribe (STT) ----
# transcriber now accepts raw bytes directly, no temp file needed.
transcription = transcriber.transcribe(
    audio_path=audio_bytes,
    lang_code="hi",
    decoder="rnnt",  # best for elder speech
)
print("📝 Transcription:", transcription)

# ---- Step 3: Generate response audio (TTS) ----
tts_result = tts_generator.generate(
    prompt=transcription,
    output_path=LOCAL_OUTPUT_PATH,
)
print(f"🔊 Generated {tts_result['duration']:.2f}s audio in {tts_result['elapsed_time']:.2f}s")

# ---- Step 4: Upload output audio to S3 (simple filename, not a long uuid) ----
output_storage_path = f"{USER_ID}/tts/{THREAD_ID}/output.wav"
with open(LOCAL_OUTPUT_PATH, "rb") as f:
    supabase_client.storage.from_(BUCKET_NAME).upload(
        output_storage_path, f.read(), file_options={"content-type": "audio/wav"}
    )
print(f"✅ TTS audio uploaded -> {output_storage_path}")