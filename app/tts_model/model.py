import os
from pathlib import Path
import time
from typing import Optional, Union
from parler_tts import ParlerTTSForConditionalGeneration
import soundfile as sf
import torch
from transformers import AutoTokenizer

# 1. Device configuration
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "ai4bharat/indic-parler-tts"

# 2. Global load on module import (runs once)
print(f"Loading Indic-Parler-TTS model ({MODEL_NAME}) on {DEVICE}...")
indic_tts_model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEVICE)
indic_tts_model.eval()

tts_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
desc_tokenizer = AutoTokenizer.from_pretrained(indic_tts_model.config.text_encoder._name_or_path)


# 3. TTS Class
class IndicTTSGenerator:
    """TTS generation wrapper using globally loaded Indic-Parler-TTS."""

    def __init__(
        self,
        model: ParlerTTSForConditionalGeneration = indic_tts_model,
        tokenizer: AutoTokenizer = tts_tokenizer,
        description_tokenizer: AutoTokenizer = desc_tokenizer,
        device: str = DEVICE,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.description_tokenizer = description_tokenizer
        self.device = device
        self.sampling_rate: int = self.model.config.sampling_rate

    @torch.inference_mode()
    def generate(
        self,
        prompt: str,
        description: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> dict:
        """Generates speech for a single text prompt based on a voice description.

        Args:
            prompt: The text to be spoken.
            description: Voice style description (speaker gender, pace, pitch,
              accent).
            output_path: Optional file path to write the generated .wav file.

        Returns:
            Dictionary containing the audio array, sample rate, duration, and
            generation latency.
        """
        # Tokenize inputs
        desc_inputs = self.description_tokenizer(description, return_tensors="pt").to(self.device)
        prompt_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start_time = time.perf_counter()

        # Generate audio tokens
        generation = self.model.generate(
            input_ids=desc_inputs.input_ids,
            attention_mask=desc_inputs.attention_mask,
            prompt_input_ids=prompt_inputs.input_ids,
            prompt_attention_mask=prompt_inputs.attention_mask,
        )

        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed_time = time.perf_counter() - start_time

        # Convert to 1D numpy array
        audio_arr = generation.cpu().numpy().squeeze()
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