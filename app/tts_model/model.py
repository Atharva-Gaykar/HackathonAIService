import time
from pathlib import Path
from typing import Optional, Union

import soundfile as sf
import torch
from transformers import AutoModel, AutoTokenizer

# 1. Device configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "ai4bharat/vits_rasa_13"

# 2. Global load on module import (runs once)
print(f"Loading VITS-Rasa TTS model ({MODEL_NAME}) on {DEVICE}...")
vits_tts_model = AutoModel.from_pretrained(
    MODEL_NAME, trust_remote_code=True
).to(DEVICE)
vits_tts_model.eval()

vits_tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME, trust_remote_code=True
)

# Defaults used when caller doesn't override — from the ai4bharat example
DEFAULT_SPEAKER_ID = 16  # PAN_M
DEFAULT_STYLE_ID = 0     # ALEXA


# 3. TTS Class
class IndicTTSGenerator:
    """TTS generation wrapper using the globally loaded VITS-Rasa model.

    generate(prompt, description, output_path) keeps the exact same
    signature as the previous Parler-TTS version, so main.py does not
    need to change. VITS-Rasa has no free-text voice-description input
    though (it uses numeric speaker_id / style_id instead) — so
    `description` is accepted here purely for interface compatibility
    and is not used. Pass speaker_id / style_id explicitly if you need
    to pick a voice other than the defaults.
    """

    def __init__(
        self,
        model: torch.nn.Module = vits_tts_model,
        tokenizer: AutoTokenizer = vits_tokenizer,
        device: str = DEVICE,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.sampling_rate: int = self.model.config.sampling_rate

    @torch.inference_mode()
    def generate(
        self,
        prompt: str,
        description: Optional[str] = None,  # unused — kept for call-site compatibility
        output_path: Optional[Union[str, Path]] = None,
        speaker_id: int = DEFAULT_SPEAKER_ID,
        style_id: int = DEFAULT_STYLE_ID,
    ) -> dict:
        """Generates speech for a single text prompt.

        Args:
            prompt: The text to be spoken.
            description: Ignored — VITS-Rasa has no free-text voice
              description input. Kept so existing callers passing this
              (e.g. main.py's `voice_desc`) don't need to change.
            output_path: Optional file path to write the generated .wav file.
            speaker_id: Numeric speaker id (see model card for the full list).
            style_id: Numeric emotion/style id (see model card for the full list).

        Returns:
            Dictionary containing the audio array, sample rate, duration, and
            generation latency — same shape as the previous implementation.
        """
        inputs = self.tokenizer(text=prompt, return_tensors="pt").to(self.device)

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start_time = time.perf_counter()

        outputs = self.model(
            inputs["input_ids"],
            speaker_id=speaker_id,
            emotion_id=style_id,
        )

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed_time = time.perf_counter() - start_time

        # Move waveform to CPU and convert to numpy
        audio_arr = outputs.waveform.squeeze().cpu().numpy()
        duration = len(audio_arr) / self.sampling_rate
        rtf = elapsed_time / duration if duration > 0 else 0.0

        # Save to disk if output path is provided
        if output_path:
            save_path = Path(output_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(save_path), audio_arr, self.sampling_rate)

        return {
            "audio": audio_arr,
            "sampling_rate": self.sampling_rate,
            "duration": duration,
            "elapsed_time": elapsed_time,
            "rtf": rtf,
            "saved_path": str(output_path) if output_path else None,
        }


# 4. Ready-to-use instance
tts_generator = IndicTTSGenerator()