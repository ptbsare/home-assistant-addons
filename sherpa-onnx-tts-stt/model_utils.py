# sherpa-onnx-tts-stt/model_utils.py
import os
import subprocess
import logging
import sherpa_onnx
_LOGGER = logging.getLogger("sherpa_onnx_model_utils")

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
    
def initialize_models(cli_args):
    """Initializes STT and TTS models based on CLI arguments."""

    stt_model_dir = "/stt-models"
    tts_model_dir = "/tts-models"

    # Prepare Models
    if cli_args.custom_stt_model != 'null':
        _initialize_stt_models(stt_model_dir, cli_args.custom_stt_model)

    if cli_args.custom_tts_model != 'null':
        _initialize_tts_models(tts_model_dir, cli_args.custom_tts_model)

    # STT Initialization (adjust paths as needed for extracted model)
    if cli_args.custom_stt_model_eval != 'null':
        try:
            stt_model = eval(cli_args.custom_stt_model_eval)
        except Exception as e:
            _LOGGER.exception("Failed to initialize custom STT model:")
            raise
    else:
        if 'sherpa-onnx-paraformer-zh-2023-03-28' == cli_args.stt_model:
            try:
                stt_model = sherpa_onnx.OfflineRecognizer.from_paraformer(
                    paraformer=os.path.join(stt_model_dir, cli_args.stt_model,
                                            "model.int8.onnx" if cli_args.stt_use_int8_onnx_model == True else "model.onnx"),
                    tokens=os.path.join(stt_model_dir, cli_args.stt_model, "tokens.txt"),
                    decoding_method='greedy_search',
                    provider=cli_args.provider,
                    num_threads=cli_args.stt_thread_num,  # Adjust based on your hardware
                    sample_rate=16000,
                    feature_dim=80,
                    debug=cli_args.debug,
                )
            except Exception as e:  # More specific exception handling is better
                _LOGGER.exception("Failed to initialize STT model:")
                raise

        elif 'sherpa-onnx-paraformer-zh-small-2024-03-09' == cli_args.stt_model:
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
                raise
        else:
            stt_model = None

    # TTS Initialization
    if cli_args.custom_tts_model_eval != 'null':
        try:
            tts_model = eval(cli_args.custom_tts_model_eval)
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
                                vocoder=os.path.join(tts_model_dir, "hifigan_v2.onnx"),
                                lexicon=os.path.join(tts_model_dir, cli_args.tts_model, "lexicon.txt"),
                                tokens=os.path.join(tts_model_dir, cli_args.tts_model, "tokens.txt"),
                                data_dir=os.path.join(tts_model_dir, "espeak-ng-data"),
                                dict_dir=os.path.join(tts_model_dir, cli_args.tts_model, "dict"),
                            ),
                            provider=cli_args.provider,  # or "cuda" if you have a GPU
                            num_threads=cli_args.tts_thread_num,  # Adjust as needed
                            debug=cli_args.debug,  # Set to True for debugging output
                        ),
                        rule_fsts=f"{tts_model_dir}/{cli_args.tts_model}/phone.fst,{tts_model_dir}/{cli_args.tts_model}/date.fst,{tts_model_dir}/{cli_args.tts_model}/number.fst",  # Example rule FSTs, adjust path if needed
                        max_num_sentences=1,
                    )
                )
            except Exception as e:
                _LOGGER.exception("Failed to initialize TTS model:")
                raise

        elif 'vits-melo-tts-zh_en' == cli_args.tts_model:
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
        elif 'kokoro-int8-multi-lang-v1_1' == cli_args.tts_model:
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
        else:
            tts_model = None

    return stt_model, tts_model