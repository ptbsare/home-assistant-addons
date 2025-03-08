from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import numpy as np
import io
from typing import Optional, Any
import logging
from pydub import AudioSegment  # Import pydub
#from run import model_container # Removed circular import
from model_container import ModelContainer
from pydantic import Field

# Global variable to hold the models (will be initialized in run.py)
_model_container: ModelContainer = None

def get_models() -> ModelContainer:
    # Use the global _model_container
    if _model_container is None:
      raise Exception("Model container not initialized")
    return _model_container

app = FastAPI()
_LOGGER = logging.getLogger("sherpa_onnx_api")

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    _LOGGER.debug("Middleware called")  # Simple log message
    response = await call_next(request)
    return response

class TranscribeRequest(BaseModel):
    file: bytes
    language: Optional[str] = None


@app.post("/v1/audio/transcriptions")
async def transcribe_audio(request: Request, file: UploadFile = File(...), language: Optional[str] = None, models: ModelContainer = Depends(get_models)):
    _LOGGER.debug(f"Received request: {request.method} {request.url}")
    _LOGGER.debug(f"Headers: {request.headers}")
    try:
        contents = await file.read()
        _LOGGER.debug(f"Body (truncated): {contents[:100]}...")  # Log truncated body

        # Use pydub to read the audio file (handles format detection)
        audio = AudioSegment.from_file(io.BytesIO(contents))

        # Convert to 16kHz, mono, 16-bit PCM
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)

        # Get raw audio data as bytes
        audio_data = audio.raw_data

        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        stream = models.stt_model.create_stream()
        stream.accept_waveform(16000, audio_array)
        models.stt_model.decode_stream(stream)
        result = stream.result

        if result and result.text:
            return {"text": result.text}
        else:
            return {"text": ""}

    except Exception as e:
        _LOGGER.exception(f"Error during STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))
class TTSRequest(BaseModel):
    text: str = Field(..., alias="input")
    model: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None


@app.post("/v1/audio/speech")
async def generate_speech(request: Request, tts_request: TTSRequest, models: ModelContainer = Depends(get_models)):
    _LOGGER.debug(f"Received request: {request.method} {request.url}")
    _LOGGER.debug(f"Headers: {request.headers}")
    _LOGGER.debug(f"Body: {tts_request.dict()}")

    try:
        # Use provided values or defaults
        speaker_id = 0
        if tts_request.voice is not None and tts_request.voice == "aishell3":
            speaker_id = 0

        speed = tts_request.speed if tts_request.speed is not None else 1.0
        _LOGGER.debug(f"TTS Request: text={tts_request.text}, speaker_id={speaker_id}, speed={speed}")

        audio = models.tts_model.generate(
            text=tts_request.text,
            sid=speaker_id,
            speed=speed,
        )
        if isinstance(audio.samples, (list, np.ndarray)):
            audio_samples = np.array(audio.samples, dtype=np.float32)
        else:
            raise TypeError(
                "Unexpected type for audio.samples: {}".format(type(audio.samples))
            )
        audio_samples = (audio_samples * 32767).astype(np.int16)
        audio_bytes = audio_samples.tobytes()

        # Construct WAV header
        sample_rate = int(audio.sample_rate)  # Ensure it's an integer
        num_channels = 1
        bits_per_sample = 16
        subchunk2_size = len(audio_bytes)
        chunk_size = 36 + subchunk2_size
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8

        header = b'RIFF'
        header += chunk_size.to_bytes(4, 'little')
        header += b'WAVE'
        header += b'fmt '
        header += (16).to_bytes(4, 'little')  # Subchunk1Size (PCM)
        header += (1).to_bytes(2, 'little')  # AudioFormat (PCM)
        header += num_channels.to_bytes(2, 'little')
        header += sample_rate.to_bytes(4, 'little')
        header += byte_rate.to_bytes(4, 'little')
        header += block_align.to_bytes(2, 'little')
        header += bits_per_sample.to_bytes(2, 'little')
        header += b'data'
        header += subchunk2_size.to_bytes(4, 'little')

        # Combine header and audio data
        wav_data = header + audio_bytes

        headers = {
            "Content-Type": "audio/wav",
            "Content-Security-Policy": "media-src * data: blob:;"
        }
        return StreamingResponse(io.BytesIO(wav_data), media_type="audio/wav", headers=headers)

    except Exception as e:
        _LOGGER.exception(f"Error during TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    

@app.get("/health")
async def health_check():
    return {"status": "ok"}

