# Automation Builder

**Use an LLM chat to execute web navigation commands and actions** through your real logged-in browser.

> Powered by **CDP-connected Playwright** (your real logged-in Chrome), **visual observability** (glowing panda), **keyboard-level control**, and **swarm-style agent patterns** inspired by [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm).

**Core repo concept**: Chat naturally with an LLM. The model translates your intent into precise browser actions using the full power of Automation Builder.

This is the flagship experience of the project.

## The Vision

Instead of writing brittle scripts or using fragile headless automation, you simply talk to your browser:

- "Go to Hugging Face, search for the latest Llama 3.2 GGUF models, and open the top result"
- "Log into Linear, create a new issue titled 'Fix the panda animation', and assign it to me"
- "On GitHub, create a new public repo called 'my-automation-experiments' with Python .gitignore and MIT license"

The LLM uses the rich, observable, keyboard-friendly surface provided by the connector (including the powerful `select` command for dropdowns).

## Flagship Feature: LLM Chat

The main entrypoint is `llm_chat.py`:

```bash
python llm_chat.py
```

It connects to:
- Your real Chrome (via CDP on port 9222)
- A local LLM via Ollama (default: llama3.1 or similar)

The agent has full access to the connector's capabilities and automatically shows the glowing panda while acting.

See `llm_chat.py` for the current implementation (ReAct-style action parsing + strong system prompt).

## Why This Approach Works

- Real browser = real logins, real state, real extensions
- Glowing panda = excellent observability for the LLM (and for you watching)
- Keyboard + `select_option` + `list_keyboard_shortcuts()` = reliable, discoverable actions
- JSON-friendly output + structured results = easy for LLMs to reason over

## Quick Start

```bash
# 1. Start your persistent Chrome
python browser_connector.py launch-browser

# 2. (Optional) Start Ollama with a good model
ollama run llama3.1

# 3. Launch the LLM chat
python llm_chat.py
```

Then just talk to it. The model will drive the browser for you.

## Examples

```bash
# Python API
conn = WebBrowserConnector(cdp_url="http://localhost:9222", auto_indicator=True)
conn.goto("https://github.com/new")
conn.select_option("Python", container="Add .gitignore")
conn.select_option("MIT License", container="Add license")

# CLI
python browser_connector.py select "Public" --container "Choose visibility"
```

See the `examples/` directory for more runnable demonstrations.

## Browser Assistant Swarm Connection

This project draws heavily from the [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm) / OpenComet architecture:

- Real browser as a first-class tool for agents
- Strong observability and structured action surface
- Designed for multi-step, long-horizon automation loops
- Excellent backend for local LLM + LangGraph browser agents

## ForgeAI Governance

This repository follows **ForgeAI v2.1** professional engineering governance.

All AI agents working in this repo must follow the process defined in [AGENTS.md](./AGENTS.md).

## Installation

```bash
pip install playwright
playwright install chromium
```

## License

MIT

---

**Built with real logged-in browser automation, the glowing panda, and a lot of debugging against production UIs.**