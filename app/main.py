import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.stt_model import transcriber
from app.tts_model import tts_generator
from app.database.object_store import supabase_client
import uvicorn

app = FastAPI()

BUCKET_NAME = "user-audio-recordings"


class TTSRequest(BaseModel):
    text: str


@app.post("/users/{user_id}/threads/{client_thread_id}/messages/{client_msg_id}/stt")
def transcribe_message(user_id: str, client_thread_id: str, client_msg_id: str):
    """
    STT only. Path params are the three IDs the client already has —
    client_msg_id is the id it generated before uploading its audio.

    Flow: pull the client's audio from S3 -> transcribe -> return the text.
    No TTS, no DB write here.
    """
    input_path = f"{user_id}/stt/{client_thread_id}/msg_{client_msg_id}.wav"

    try:
        audio_bytes = supabase_client.storage.from_(BUCKET_NAME).download(input_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Audio not found at {input_path}: {e}")

    try:
        transcription = transcriber.transcribe(
            audio_path=audio_bytes,
            lang_code="hi",
            decoder="rnnt",  # best for elder speech
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return {
        "transcription": transcription,
        "input_audio_path": input_path,
    }


@app.post("/users/{user_id}/threads/{client_thread_id}/messages/{client_msg_id}/tts")
def generate_tts_message(user_id: str, client_thread_id: str, client_msg_id: str, payload: TTSRequest):
    """
    TTS only. client_msg_id here is NOT server-generated — the client already
    created the message row (type='tts') and got this id back from that save,
    so we reuse it as the S3 filename to keep the DB row and the S3 object
    in sync.
    """
    local_output_path = f"temp_{client_msg_id}.wav"

    try:
        tts_result = tts_generator.generate(
            prompt=payload.text,
            output_path=local_output_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    output_storage_path = f"{user_id}/tts/{client_thread_id}/msg_{client_msg_id}.wav"

    try:
        with open(local_output_path, "rb") as f:
            supabase_client.storage.from_(BUCKET_NAME).upload(
                output_storage_path, f.read(), file_options={"content-type": "audio/wav"}
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upload to S3 failed: {e}")
    finally:
        os.remove(local_output_path)

    return {
        "output_audio_path": output_storage_path,
        "duration_seconds": round(tts_result["duration"], 2),
    }

if __name__ == "__main__":
  
    uvicorn.run("app.main:app", host="127.0.0.1", port=8500)