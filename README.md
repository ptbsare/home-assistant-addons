# Home Assistant Add-on: ptbsare

ptbsare's Add-ons for [Home Assistant](https://www.home-assistant.io).

# Sherpa Onnx TTS/STT

  Sherpa-onnx TTS/STT with wyoming support, supports kokoro-TTS/matcha-TTS/paraformer-STT, requires 1.5GB RAM. 
  
  离线Sherpa-onnx TTS/STT的wyoming集成，支持kokoro-TTS/matcha-TTS/paraformer-STT，需要1.5G内存。
  
  Also supports Openai-format TTS/STT api  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions
  
  同时支持Openai TTS/STT 格式两个接口  IP:10500/v1/audio/speech IP:10500/v1/audio/transcriptions

  See [DOCS.md](https://github.com/ptbsare/sherpa-onnx-tts-stt/blob/main/DOCS.md) for documentation.

  文档见 [DOCS.md](https://github.com/ptbsare/sherpa-onnx-tts-stt/blob/main/DOCS.md)

[![Show add-on](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=adfd7a46_sherpa_onnx_tts_stt&repository_url=https%3A%2F%2Fgithub.com%2Fptbsare%2Fhome-assistant-addons)

  ([Sherpa Onnx Github Page](https://github.com/k2-fsa/sherpa-onnx))


# MCP Proxy Server

A central hub for Model Context Protocol (MCP) servers. Manages multiple backend MCP servers (Stdio/SSE), exposing their combined tools and resources via a unified SSE interface or as a Stdio server.

一个模型上下文协议 (MCP) 服务器的中心枢纽。管理多个后端 MCP 服务器 (Stdio/SSE)，通过统一的 SSE 接口或作为 Stdio 服务器暴露其组合的工具和资源。

**Key Features:** / **主要特性:**
*   **Web UI Management:** Easily manage connected MCP servers and tools via an intuitive web interface. / **网页界面管理:** 通过直观的网页界面轻松管理连接的 MCP 服务器和工具。
*   **Granular Tool Control:** Enable/disable individual tools and override their names/descriptions. / **精细工具控制:** 启用/禁用单个工具，并覆盖其名称/描述。
*   **Real-time Install Monitoring:** Track Stdio server installation progress directly in the Web UI. / **实时安装监控:** 直接在网页界面中跟踪 Stdio 服务器的安装进度。
*   **Optional Web Terminal:** Access a command-line terminal within the Admin UI for direct interaction. / **可选网页终端:** 在管理界面中访问命令行终端进行直接交互。

See [DOCS.md](mcp-proxy-server/DOCS.md) for documentation.

文档见 [DOCS.md](mcp-proxy-server/DOCS.md)

[![Show add-on](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=mcp_proxy_server&repository_url=https%3A%2F%2Fgithub.com%2Fptbsare%2Fhome-assistant-addons)

([MCP Proxy Server Code](mcp-proxy-server/)) / ([MCP Proxy Server 代码](mcp-proxy-server/))