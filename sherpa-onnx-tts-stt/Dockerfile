ARG BUILD_FROM "python:3.11.9-slim-bullseye"
FROM $BUILD_FROM
ENV LANGUAGE='zh-CN'
ENV SPEED='1.0'
ENV STT_MODEL='sherpa-onnx-paraformer-zh-2023-03-28'
ENV STT_USE_INT8_ONNX_MODEL='True'
ENV STT_THREAD_NUM='3'
ENV TTS_MODEL='matcha-icefall-zh-baker'
ENV TTS_THREAD_NUM='3'
ENV TTS_SPEAKER_SID='0'
ENV DEBUG='False'
ENV CUSTOM_STT_MODEL='null'
ENV CUSTOM_STT_MODEL_EVAL='null'
ENV CUSTOM_TTS_MODEL='null'
ENV CUSTOM_TTS_MODEL_EVAL='null'
# Install Python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat-traditional \
        tar \
        curl \
        bzip2 \
        git \
        cython3 \
        python3-pip \
        python3 \
        ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /
COPY rootfs/etc /etc

# Create model directories
RUN mkdir -p /stt-models && mkdir -p /tts-models

# Download and extract builtin STT model
WORKDIR /stt-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 -o sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 && \
    tar -xf sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 && \
    rm sherpa-onnx-paraformer-zh-2023-03-28.tar.bz2 

RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 -o sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 && \
    tar -xf sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 && \
    rm sherpa-onnx-paraformer-zh-small-2024-03-09.tar.bz2 

# Download and extract builtin TTS model
WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2 -o matcha-icefall-zh-baker.tar.bz2 && \
    tar -xf matcha-icefall-zh-baker.tar.bz2 && \
    rm matcha-icefall-zh-baker.tar.bz2 

WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-multi-lang-v1_1.tar.bz2 -o kokoro-int8-multi-lang-v1_1.tar.bz2 && \
    tar -xf kokoro-int8-multi-lang-v1_1.tar.bz2 && \
    rm kokoro-int8-multi-lang-v1_1.tar.bz2 

WORKDIR /tts-models
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2 -o vits-melo-tts-zh_en.tar.bz2 && \
    tar -xf vits-melo-tts-zh_en.tar.bz2 && \
    rm vits-melo-tts-zh_en.tar.bz2 

RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v1.onnx -o hifigan_v1.onnx    
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v2.onnx -o hifigan_v2.onnx
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/hifigan_v2.onnx -o hifigan_v3.onnx

# Download and extract espeak-ng-data
WORKDIR /tts-models/espeak-ng-data
RUN curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/espeak-ng-data.tar.bz2 -o espeak-ng-data.tar.bz2 && \
    tar -xf espeak-ng-data.tar.bz2 && \
    rm espeak-ng-data.tar.bz2   

HEALTHCHECK --start-period=3m --interval=30m \
    CMD echo '{ "type": "describe" }' \
        | nc -w 1 localhost 10400 \
        | grep -iq "Sherpa" \
        || exit 1
# Copy the add-on code.  Crucially *before* requirements.txt, so Docker layer caching works!
COPY . /app
WORKDIR /app
RUN ls -la /app
# Install Python dependencies
# Install sherpa-onnx.  Make sure ARM architecture is handled correctly.
#RUN pip3 install --no-cache-dir sherpa-onnx
RUN pip install --break-system-packages --no-cache-dir sherpa-onnx numpy
#-f https://k2-fsa.github.io/sherpa/onnx/cpu.html
#install 
RUN pip install --break-system-packages --no-cache-dir git+https://github.com/rhasspy/wyoming.git

#EXPOSE PORTS
EXPOSE 10400 10500
RUN pip install --break-system-packages --no-cache-dir uvicorn fastapi pydantic pydub python-multipart






