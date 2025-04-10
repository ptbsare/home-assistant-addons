# Changelog

## 0.2.7

- Experimental Support for custom_tts/stt_model and downloading models on the fly, see DOCS.md.
- Fix debug switch.
- Update documents.
- 对自定义模型的实验性支持，支持用户自定义模型及参数，运行时自动下载并解压模型，详见文档。
- 修复debug开关不生效。
- 更新文档。

## 0.2.8

- Bug Fix: Fix kokora-tts_v1 tts.
- 修复kokora-tts_v1 bug

## 0.2.9

- Add GPU Support. (See Dockerfile.gpu)
- fix custom_models for addon
- Builtin stt model sherpa-onnx-paraformer-zh-small-2024-03-09
- Builtin tts model vits-melo-tts-zh_en
- 实验性添加GPU支持。（见Dockerfile.gpu）
- 修复addon的custom_models参数
- 内置stt模型sherpa-onnx-paraformer-zh-small-2024-03-09
- 内置tts模型vits-melo-tts-zh_en


## 0.2.10

- Bump Kokoro-TTS to v1.1
- 升级内置Kokoro-TTS到v1.1

## 0.3.0

- Experimental Support for Openai-format TTS/STT api  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions
- 添加Openai兼容格式 TTS/STT 实验性支持，实现了两个接口  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions

## 0.3.1

- Fix void STT result bug (result in Wyoming Satellite hang).
- 修复STT结果为空导致语音助手阻塞的bug.
- Set debug to false by default.
- 默认关闭debug日志减少日志输出。