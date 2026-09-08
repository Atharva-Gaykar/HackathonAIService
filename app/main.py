from app.stt_model import transcriber
from app.tts_model import tts_generator
from app.database.object_store import supabase



# Example: upload or query directly using the client
buckets = supabase.storage.list_buckets()
audio_file = "Audio Samples/Hindi Sample.wav"

# Transcribe directly using the pre-initialized instance
result = transcriber.transcribe(
    audio_path=audio_file,
    lang_code="hi",
    decoder="rnnt",  # Best for elder speech
)

print("Transcription:", result)


# Single clip generation
prompt_text = "नमस्ते, आप कैसे हैं?"
voice_desc = "A male speaker delivers a slow and clear speech with a calm tone in a quiet environment."

result = tts_generator.generate(
    prompt=prompt_text,
    description=voice_desc,
    output_path="tts_outputs/sample_hindi.wav",
)

print(f"Generated {result['duration']:.2f}s audio in {result['elapsed_time']:.2f}s")
print(f"Saved at: {result['saved_path']}")