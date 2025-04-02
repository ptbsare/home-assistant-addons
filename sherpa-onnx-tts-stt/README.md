# Home Assistant Add-on: Sherpa Onnx TTS/STT

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield]

Supports Kokoro-TTS!!

Offline Sherpa-onnx TTS/STT with wyoming support, supports kokoro-TTS/matcha-TTS/paraformer-STT, requires 1.5GB RAM. 
  
离线Sherpa-onnx TTS/STT的wyoming集成，支持kokoro-TTS/matcha-TTS/paraformer-STT，需要1.5G内存。

Also supports Openai-format TTS/STT api  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions

同时支持Openai TTS/STT 格式两个接口  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions
(It just works. PR is welcomed to improve this.)

## Supported STT Models:
* sherpa-onnx-paraformer-zh-2023-03-28 (Chinese Only, very fast on Intel(R) Celeron(R) CPU N3350 @ 1.10GHz)
* sherpa-onnx-paraformer-zh-small-2024-03-09 (Chinese Only, very fast on Intel(R) Celeron(R) CPU N3350 @ 1.10GHz)

## Supported TTS Models:
* matcha-icefall-zh-baker (Chinese Only, fast on Intel(R) Celeron(R) CPU N3350 @ 1.10GHz)
* vits-melo-tts-zh_en (Chinese and English, medium on Intel(R) Celeron(R) CPU N3350 @ 1.10GHz)
* kokoro-multi-lang-v1_0 (Multiple-Languages, a little bit slow on Intel(R) Celeron(R) CPU N3350 @ 1.10GHz)
```
For kokoro-multi-lang-v1_1
There are 53 speakers in the model, with speaker ID 0 -- 52.

The mapping between speaker ID (AKA sid ) and speaker name is given below:

0->af_alloy, 1->af_aoede, 2->af_bella, 3->af_heart, 4->af_jessica, 5->af_kore, 6->af_nicole, 7->af_nova, 
8->af_river, 9->af_sarah, 10->af_sky, 11->am_
adam, 12->am_echo, 13->am_eric, 14->am_fenrir, 15->am_liam, 16->am_michael, 
17->am_onyx, 18->am_puck, 19->am_santa, 20->bf_alice, 21->bf_emma, 22->bf_
isabella, 23->bf_lily, 24->bm_daniel, 25->bm_fable, 26->bm_george, 27->bm_lewis, 
28->ef_dora, 29->em_alex, 30->ff_siwis, 31->hf_alpha, 32->hf_beta, 33
->hm_omega, 34->hm_psi, 35->if_sara, 36->im_nicola, 37->jf_alpha, 
38->jf_gongitsune, 39->jf_nezumi, 40->jf_tebukuro, 41->jm_kumo, 
42->pf_dora, 43->pm_alex, 44->pm_santa, 45->zf_xiaobei, 46->zf_xiaoni, 
47->zf_xiaoxiao, 
48->zf_xiaoyi, 49->zm_yunjian, 50->zm_yunxi, 51->zm_yunxia, 52->zm_yunyang,

```

## Custom Models are supportted.
See [DOCS.md](https://github.com/ptbsare/home-assistant-addons/blob/main/sherpa-onnx-tts-stt/DOCS.md) for documentation.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-no-red.svg
[armv7-shield]: https://img.shields.io/badge/armv7-no-red.svg
[i386-shield]: https://img.shields.io/badge/i386-no-red.svg
