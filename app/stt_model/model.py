import io
from pathlib import Path
from typing import BinaryIO, Union

import soundfile as sf
import torch
import torchaudio
from transformers import AutoModel


#  Global Setup and Model Loading (Executed Once at Module Load)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_NAME = "ai4bharat/indic-conformer-600m-multilingual"

print(f"Loading  model '{MODEL_NAME}' on {DEVICE}...")
MODEL = AutoModel.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
).to(DEVICE)
MODEL.eval()


AudioInput = Union[str, Path, bytes, BinaryIO]


# Transcriber Class
class IndicASRTranscriber:
    """ASR handler utilizing the globally loaded IndicConformer model."""

    TARGET_SAMPLE_RATE: int = 16000
    SUPPORTED_DECODERS: tuple[str, ...] = ("ctc", "rnnt")

    def __init__(self, model: torch.nn.Module = MODEL, device: torch.device = DEVICE):
        # Uses the globally loaded model by default; avoids any reloading
        self.model = model
        self.device = device

    def preprocess_audio(self, audio_path: AudioInput) -> torch.Tensor:
        if isinstance(audio_path, (str, Path)):
            path = Path(audio_path)
            if not path.is_file():
                raise FileNotFoundError(f"Audio file not found at: {path.resolve()}")
            source = str(path)
        elif isinstance(audio_path, bytes):
            source = io.BytesIO(audio_path)
        else:
            # already file-like (e.g. io.BytesIO)
            source = audio_path

        audio_data, sr = sf.read(source)
        wav = torch.tensor(audio_data, dtype=torch.float32)

        # Convert multi-channel to mono
        if wav.ndim > 1:
            wav = torch.mean(wav, dim=1)

        # Shape: [1, samples]
        wav = wav.unsqueeze(0)

        # Resample to 16 kHz if necessary
        if sr != self.TARGET_SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sr,
                new_freq=self.TARGET_SAMPLE_RATE,
            )
            wav = resampler(wav)

        return wav.to(self.device)

    @torch.inference_mode()
    def transcribe(
        self,
        audio_path: AudioInput,
        lang_code: str = "hi",
        decoder: str = "ctc",
    ) -> str:
        decoder = decoder.lower()
        if decoder not in self.SUPPORTED_DECODERS:
            raise ValueError(f"Invalid decoder '{decoder}'. Choose: {self.SUPPORTED_DECODERS}")

        wav = self.preprocess_audio(audio_path)
        transcription = self.model(wav, lang_code, decoder)

        if isinstance(transcription, (list, tuple)):
            return transcription[0]
        return transcription


# singleton instance
transcriber = IndicASRTranscriber()