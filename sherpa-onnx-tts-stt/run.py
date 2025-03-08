# Home Assistant Add-on: sherpa-onnx-tts-stt

# Standard library imports
import logging
import os
import subprocess  # For running shell commands to download models
import asyncio
import argparse
from functools import partial
import numpy as np
import math

# Third-party library imports
from wyoming.asr import (
    Transcribe,
    Transcript,
)

from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
#from wyoming.config import PipelineConfig, load_config
from wyoming.event import Event
from wyoming.info import  AsrModel, AsrProgram, TtsVoice, TtsProgram, Describe, Info, Attribution
from wyoming.server import AsyncEventHandler, AsyncServer, AsyncTcpServer
from wyoming.tts import Synthesize

import sherpa_onnx

_LOGGER = logging.getLogger("sherpa_onnx_addon")


def _download_model(model_url, model_dir, model):
        """Downloads and extracts the model."""
        if not os.path.exists(os.path.join(model_dir, model)):
            _LOGGER.info(f"Downloading model: {model_url}")
            os.makedirs(os.path.join(model_dir, model), exist_ok=True)

            # Use curl (or wget) for download and extraction (more robust than Python libraries for large files)
            try:
                subprocess.check_call(
                   ["curl", "-L", model_url, "-o", os.path.join(model_dir, model, f"{model}.tar.gz")]
                )
                _LOGGER.info(f"Downloaded model: {model_url}, Extracting...")
                subprocess.check_call(["tar", "-xvf", os.path.join(model_dir, model, f"{model}.tar.gz"),"-C", model_dir])
                os.remove(os.path.join(model_dir, model, f"{model}.tar.gz")) # Clean up
                _LOGGER.info(f"Download and extract Done. Cleaned up.")
            except subprocess.CalledProcessError as e:
                _LOGGER.error(f"Error downloading or extracting  model: {e}")
                raise  #  Re-raise to stop add-on startup on failure
        else:
            _LOGGER.info(f"{model} model already exists.")

def _initialize_stt_models(stt_model_dir, model):
        # --- STT Model ---
        stt_model_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{model}.tar.bz2"
        _download_model(stt_model_url, stt_model_dir, model)

def _initialize_tts_models(tts_model_dir, model):
        # --- TTS Model ---
        tts_model_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{model}.tar.bz2"
        _download_model(tts_model_url, tts_model_dir, model)

class SherpaOnnxEventHandler(AsyncEventHandler):
    """Event handler for sherpa-onnx TTS and STT."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args,  # For language/speed settings
        tts_model,
        stt_model,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.wyoming_info_ = wyoming_info

#        self.config = load_config()
#        self.pipeline_config: PipelineConfig = self.config.pipelines[
#            self.cli_args.pipeline
#        ]

        _LOGGER.debug(f"CLI Args: {self.cli_args}")

        self.tts_model = tts_model

        self.stt_model = stt_model

        self.audio_converter = AudioChunkConverter(rate=16000, width=2, channels=1)
        self.audio = b""




        
    async def initialize(self) -> None:
           """ Async initialization (if needed, after models are loaded) """
           pass


    async def handle_event(self, event: Event) -> bool:
        """Handles a single event."""
        _LOGGER.debug(f"Received event: {event}") # important for debugging
        if Describe.is_type(event.type):
            await self.write_event(self.wyoming_info_.event())
            _LOGGER.debug(f"Sent info:{self.wyoming_info_.event()}")
            return True  # Stop other handlers


        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            audio = self.tts_model.generate(
                text=synthesize.text,
                sid=self.cli_args.tts_speaker_sid,
                speed=self.cli_args.speed,
            )
            _LOGGER.debug(f"Synthesizing: {synthesize.text}")
            if isinstance(audio.samples, list):
                audio_samples = np.array(audio.samples, dtype=np.float32)
            elif isinstance(audio.samples, np.ndarray):
                audio_samples = audio.samples.astype(np.float32) # Ensure float32
            else:
                raise TypeError("Unexpected type for audio.samples: {}".format(type(audio.samples)))

            # Scale to int16 and convert to bytes
            audio_samples = (audio_samples * 32767).astype(np.int16)
            audio_bytes = audio_samples.tobytes()
            # Send AudioStart
            await self.write_event(
                AudioStart(
                    rate=audio.sample_rate,
                    width=2,
                    channels=1
                ).event()
            )
            _LOGGER.debug("Sent Audio Start")
            # Send TTS Chunk (raw audio)
            bytes_per_chunk = 1024;
            num_chunks = int(math.ceil(len(audio_bytes) / bytes_per_chunk))

            # Split into chunks
            for i in range(num_chunks):
                offset = i * bytes_per_chunk
                chunk = audio_bytes[offset : offset + bytes_per_chunk]
                await self.write_event(
                    AudioChunk(
                        audio=chunk,
                        rate=audio.sample_rate,
                        width=2,
                        channels=1,
                    ).event(),
                )
            _LOGGER.debug("Sent TTS Chunk")
            # Send Audio Stop
            await self.write_event(AudioStop().event())
            _LOGGER.debug("Sent Audio Stop")
            

            return True # We handled the event

        elif Transcribe.is_type(event.type):
                # STT (Speech-to-Text)
                transcribe: Transcribe = Transcribe.from_event(event)
                _LOGGER.debug(f"Received Transcribe request: {transcribe}")
                return True




        elif AudioStart.is_type(event.type):
                # Handle AudioStart (if needed, e.g., for resetting state)
                _LOGGER.debug(f"Received audio start event")
                audio_start = AudioStart.from_event(event)
                self.audio_recv_rate=audio_start.rate
                self.stream=self.stt_model.create_stream()
                self.audio = b""
                return True



        elif AudioChunk.is_type(event.type):
                 # Handle AudioChunk
                audio_chunk = AudioChunk.from_event(event)
                #_LOGGER.debug(f"Received audio chunk: {len(audio_chunk.audio)} bytes")

                _LOGGER.debug("Processing audio chunk...")

                # Convert to expected format.
                chunk = self.audio_converter.convert(audio_chunk)
                self.audio += chunk.audio                
                return True
        elif AudioStop.is_type(event.type):
                audio_stop = AudioStop.from_event(event)
                _LOGGER.debug(f"Recevie audio stop:{audio_stop}")
                if self.audio:
                    audio_array = np.frombuffer(self.audio, dtype=np.int16).astype(np.float32) / 32768.0
                    self.stream.accept_waveform(self.audio_recv_rate, audio_array)
                    #_LOGGER.debug(f'{audio_array}')
                    #_LOGGER.debug(f'{self.audio}')
                    self.stt_model.decode_stream(self.stream)
                    result=self.stream.result
                    _LOGGER.debug(f'{result}')


                if result and result.text:
                    await self.write_event(Transcript(text=result.text).event())
                    _LOGGER.debug(f"Final transcript on stop: {result.text}")

                return True
        return False # Unhandled events



async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipeline",
        default="default",
        help="Name of Wyoming pipeline to use",
    )
    # Add custom arguments for language and speed
    # If you want to add more options, modify: Dockerfile run.py config.yaml and sherpa-onnx-tts-stt/rootfs/etc/s6-overlay/s6-rc.d/sherpa-onnx/run
    parser.add_argument("--language", type=str, help="Language for TTS (eg: zh-CN)", default=os.environ.get('LANGUAGE'))
    parser.add_argument("--speed", type=float, help="Speed (eg: 1.0)", default=os.environ.get('SPEED'))
    parser.add_argument("--stt_model", type=str, help="STT Model", default=os.environ.get('STT_MODEL'))
    parser.add_argument("--stt_use_int8_onnx_model", type=lambda x: (str(x).lower() in ['true','1', 'yes']), help="STT Use int8 Onnx Model", default=os.environ.get('STT_USE_INT8_ONNX_MODEL'))
    parser.add_argument("--stt_thread_num", type=int, help="STT Thread Num", default=os.environ.get('STT_THREAD_NUM'))
    parser.add_argument("--tts_model", type=str, help="TTS Model", default=os.environ.get('TTS_MODEL'))
    parser.add_argument("--tts_thread_num", type=int, help="TTS Thread Num", default=os.environ.get('TTS_THREAD_NUM'))
    parser.add_argument("--tts_speaker_sid", type=int, help="TTS Speaker Sid", default=os.environ.get('TTS_SPEAKER_SID'))
    parser.add_argument("--debug", type=lambda x: (str(x).lower() in ['true','1', 'yes']), help="Enable Debug", default=os.environ.get('DEBUG'))
    parser.add_argument("--custom_stt_model", type=str, help="TTS Speaker Sid", default=os.environ.get('CUSTOM_STT_MODEL'))
    parser.add_argument("--custom_stt_model_eval", type=str, help="TTS Speaker Sid", default=os.environ.get('CUSTOM_STT_MODEL_EVAL'))
    parser.add_argument("--custom_tts_model", type=str, help="TTS Speaker Sid", default=os.environ.get('CUSTOM_TTS_MODEL'))
    parser.add_argument("--custom_tts_model_eval", type=str, help="TTS Speaker Sid", default=os.environ.get('CUSTOM_TTS_MODEL_EVAL'))

    # Wyoming Server arguments
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10400)

    # Provider arguments
    parser.add_argument("--provider", type=str, default='cpu')

    # Parse arguments
    cli_args = parser.parse_args()

    # Create the Wyoming info object.  This describes what
    #  the add-on supports.
    wyoming_info = Info(
        asr=[ 
            AsrProgram(
            name="Sherpa Onnx Offline STT",
            description="Sherpa Onnx Offline STT.",
            attribution=Attribution(
                    name="k2-fsa",
                    url="https://github.com/k2-fsa/sherpa-onnx",
                ),
            installed=True,
            version="0.0.1",
            models=[
            AsrModel(
                name=cli_args.stt_model,
                description="ASR Model.",
                languages=[cli_args.language],
                attribution=Attribution(
                    name="k2-fsa",
                    url="https://github.com/k2-fsa/sherpa-onnx",
                ),
                installed= True,  #  model is now bundled
                version="0.0.1",
        )
        ]
    )
    ],

        tts=[
            TtsProgram(
                name="Sherpa Onnx Offline TTS",
                description="Sherpa Onnx Offline TTS.",
                attribution=Attribution(
                    name="k2-fsa",
                    url="https://github.com/k2-fsa/sherpa-onnx",
                ),
                installed= True,
                version="0.0.1",
                voices=[
                    TtsVoice(
                        name=cli_args.tts_model,
                        description="TTS Model.",
                        languages=[cli_args.language],
                        attribution=Attribution(
                            name="k2-fsa",
                            url="https://github.com/k2-fsa/sherpa-onnx",
                            ),
                        installed= True,  #  model is now bundled
                        version="0.0.1",
                        )
                    ],
                )

            ]
    )

     # Set up logging
    if cli_args.debug == True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Determine Provider
    try:
        subprocess.check_output('nvidia-smi')
        _LOGGER.info('Nvidia GPU detected!')
        cli_args.provider='cuda'
    except Exception: # this command not being found can raise quite a few different errors depending on the configuration
        _LOGGER.info('No Nvidia GPU in system! CPU is used by default')
        cli_args.provider='cpu'

    _LOGGER.info("Starting sherpa-onnx add-on...")

    stt_model_dir="/stt-models"
    tts_model_dir="/tts-models"

    # Prepare Models
    if cli_args.custom_stt_model != 'null':
        _initialize_stt_models(stt_model_dir, cli_args.custom_stt_model);

    if cli_args.custom_tts_model != 'null':
        _initialize_tts_models(tts_model_dir, cli_args.custom_tts_model);

    # STT Initialization (adjust paths as needed for extracted model)
    if cli_args.custom_stt_model_eval != 'null':
        try:
            stt_model = eval(cli_args.custom_stt_model_eval);
        except Exception as e:
            _LOGGER.exception("Failed to initialize custom STT model:")
            raise
    else:
        if 'sherpa-onnx-paraformer-zh-2023-03-28' == cli_args.stt_model:
            try:
                stt_model = sherpa_onnx.OfflineRecognizer.from_paraformer(
                paraformer=os.path.join(stt_model_dir, cli_args.stt_model, "model.int8.onnx" if cli_args.stt_use_int8_onnx_model == True else "model.onnx"),
                tokens=os.path.join(stt_model_dir, cli_args.stt_model, "tokens.txt"),
                decoding_method='greedy_search',
                provider=cli_args.provider,
                num_threads=cli_args.stt_thread_num,   # Adjust based on your hardware
                sample_rate=16000,
                feature_dim=80,
                debug=cli_args.debug,
            )
            except Exception as e:  # More specific exception handling is better
                _LOGGER.exception("Failed to initialize STT model:")
                _LOGGER.error(e)
                raise

        if 'sherpa-onnx-paraformer-zh-small-2024-03-09' == cli_args.stt_model:
            try:
                stt_model = sherpa_onnx.OfflineRecognizer.from_paraformer(
                paraformer=os.path.join(stt_model_dir, cli_args.stt_model, "model.int8.onnx"),
                tokens=os.path.join(stt_model_dir, cli_args.stt_model, "tokens.txt"),
                decoding_method='greedy_search',
                provider=cli_args.provider,
                num_threads=cli_args.stt_thread_num,   # Adjust based on your hardware
                sample_rate=16000,
                feature_dim=80,
                debug=cli_args.debug,
            )
            except Exception as e:  # More specific exception handling is better
                _LOGGER.exception("Failed to initialize STT model:")
                _LOGGER.error(e)
                raise

    # TTS Initialization
    if cli_args.custom_tts_model_eval != 'null':
        try:
            tts_model = eval(cli_args.custom_tts_model_eval);
        except Exception as e:
            _LOGGER.exception("Failed to initialize custom TTS model:")
            raise
    else:
        if 'matcha-icefall-zh-baker' == cli_args.tts_model:
            try:
                tts_model = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                acoustic_model=os.path.join(tts_model_dir, cli_args.tts_model, "model-steps-3.onnx"),
                vocoder=os.path.join(tts_model_dir,"hifigan_v2.onnx"),
                lexicon=os.path.join(tts_model_dir, cli_args.tts_model, "lexicon.txt"),
                tokens=os.path.join(tts_model_dir, cli_args.tts_model, "tokens.txt"),
                data_dir=os.path.join(tts_model_dir, "espeak-ng-data"),
                dict_dir=os.path.join(tts_model_dir, cli_args.tts_model, "dict"),
                ),
                provider=cli_args.provider,    # or "cuda" if you have a GPU
                num_threads=cli_args.tts_thread_num,     # Adjust as needed
                debug=cli_args.debug,       # Set to True for debugging output
                ),
                rule_fsts=f"{tts_model_dir}/{cli_args.tts_model}/phone.fst,{tts_model_dir}/{cli_args.tts_model}/date.fst,{tts_model_dir}/{cli_args.tts_model}/number.fst",  # Example rule FSTs, adjust path if needed
                max_num_sentences=1,
                )
                )
            except Exception as e:
                _LOGGER.exception("Failed to initialize TTS model:")
                raise

        if 'vits-melo-tts-zh_en' == cli_args.tts_model:
            try:
                tts_model = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=os.path.join(tts_model_dir, cli_args.tts_model, "model.onnx"),
                lexicon=os.path.join(tts_model_dir, cli_args.tts_model, "lexicon.txt"),
                tokens=os.path.join(tts_model_dir, cli_args.tts_model, "tokens.txt"),

                dict_dir=os.path.join(tts_model_dir, cli_args.tts_model, "dict"),
                ),
                provider=cli_args.provider,
                num_threads=cli_args.tts_thread_num,
                debug=cli_args.debug,
                ),
                rule_fsts=f"{tts_model_dir}/{cli_args.tts_model}/phone.fst,{tts_model_dir}/{cli_args.tts_model}/date.fst,{tts_model_dir}/{cli_args.tts_model}/number.fst,{tts_model_dir}/{cli_args.tts_model}/new_heteronym.fst",
                max_num_sentences=1,
                )
                )
            except Exception as e:
                _LOGGER.exception("Failed to initialize TTS model:")
                raise

        if 'kokoro-int8-multi-lang-v1_1' == cli_args.tts_model:
            try:
                tts_model = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=os.path.join(tts_model_dir, cli_args.tts_model, "model.int8.onnx"),
                voices=os.path.join(tts_model_dir, cli_args.tts_model, "voices.bin"),
                lexicon=f"{tts_model_dir}/{cli_args.tts_model}/lexicon-zh.txt,{tts_model_dir}/{cli_args.tts_model}/lexicon-us-en.txt",
                tokens=os.path.join(tts_model_dir, cli_args.tts_model, "tokens.txt"),
                data_dir=os.path.join(tts_model_dir, cli_args.tts_model, "espeak-ng-data"),
                dict_dir=os.path.join(tts_model_dir, cli_args.tts_model, "dict"),
                ),
                provider=cli_args.provider,
                num_threads=cli_args.tts_thread_num,
                debug=cli_args.debug,
                ),
                rule_fsts=f"{tts_model_dir}/{cli_args.tts_model}/phone-zh.fst,{tts_model_dir}/{cli_args.tts_model}/date-zh.fst,{tts_model_dir}/{cli_args.tts_model}/number-zh.fst",
                max_num_sentences=1,
                )
                )
            except Exception as e:
                _LOGGER.exception("Failed to initialize TTS model:")
                raise


    # Create the server and handler, using our custom handler.

    # Run local server
    server = AsyncTcpServer(cli_args.host, cli_args.port)
    _LOGGER.info(f"Starting server...{cli_args.host}:{cli_args.port}")
    await server.run(
        partial(
            SherpaOnnxEventHandler,
            wyoming_info,
            cli_args,
            tts_model,
            stt_model,
            )
        )
    _LOGGER.info("Stopped")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

