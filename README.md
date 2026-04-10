# 🏔️ APEX - Multi-Provider AI Coding Assistant

![Python Version](https://img.shields.io/badge/python-3.9+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-Commercial-red?logo=law)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?logo=windows)
![Ollama](https://img.shields.io/badge/Ollama-Supported-orange?logo=ollama)
![OpenAI](https://img.shields.io/badge/OpenAI-Supported-412991?logo=openai)
![Groq](https://img.shields.io/badge/Groq-Supported-FF6B00?logo=groq)
![Status](https://img.shields.io/badge/status-Production_Ready-green)
![Version](https://img.shields.io/badge/version-1.1-blue)

## منصة برمجية ذكية متعددة المصادر - تجمع بين النماذج المحلية والسحابية

[Report Bug](https://github.com/medissaoui711/apex-core/issues) ·
[Request Feature](https://github.com/medissaoui711/apex-core/issues) ·
[Contact](https://github.com/medissaoui711)

---

## 🎯 Overview

**APEX** is a production-ready AI programming assistant that integrates:

| Component | Description |
| --------- | ----------- |
| 🏔️ **Local LLMs** | Ollama (Qwen2.5-Coder, DeepSeek, Llama3) |
| ☁️ **Cloud APIs** | OpenAI, Anthropic, Google Gemini, Groq, Together.ai |
| 🤖 **Agents** | 47 specialized agents for code review, planning, building |
| 🛠️ **Skills** | 59+ skills covering security, testing, frontend, backend |
| 📜 **Rules** | 12 coding rules for best practices |

Built for developers who want **flexibility**, **privacy**, and **power** in their AI coding workflow.

---

## 💪 Why APEX?

| Strength | Description |
| -------- | ----------- |
| 🔌 **Multi-Provider Freedom** | Use local models (free), fast cloud APIs (Groq), or premium models (OpenAI, Claude) |
| 🏔️ **Local-First Privacy** | Run entirely offline. Your code never leaves your machine |
| 🏭 **Production-Ready** | 1100+ lines of clean Python, SQLite persistence, rich CLI |
| 📚 **Rich Resource Library** | 47 agents, 59 skills, 12 rules from everything-claude-code |
| 🎮 **19 Powerful Commands** | `/plan`, `/code`, `/test`, `/review`, `/fix`, `/build`, and more |
| 🐧 **Cross-Platform** | Windows, Linux, macOS |

---

## ✨ Features

### 🔌 Multi-Provider Support

| Provider | Model | Cost | Speed |
| -------- | ----- | ---- | ----- |
| 🏔️ **Local (Ollama)** | Qwen2.5-Coder, DeepSeek, Llama3 | Free | Medium |
| 🤖 **OpenAI** | GPT-3.5/4 | Paid | Fast |
| 🧠 **Anthropic** | Claude 3 Sonnet | Paid | Medium |
| 🌐 **Google** | Gemini 1.5 Pro | Free (limited) | Fast |
| ⚡ **Groq** | Llama3 70B | Free | **Very Fast** |
| 🤝 **Together.ai** | Llama3 70B | Paid | Fast |

### 🎮 19 Commands

| Category | Commands |
| -------- | -------- |
| **Agents & Skills** | `/agents`, `/agents python`, `/skills`, `/skills all`, `/skills categories` |
| **Development** | `/plan`, `/code`, `/test`, `/review`, `/fix`, `/build` |
| **Files & Security** | `/file`, `/shield`, `/learn` |
| **Cloud** | `/provider`, `/providers` |
| **Help** | `/help`, `/quit` |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.9+
python --version

# Ollama (for local models)
curl -fsSL https://ollama.com/install.sh | sh  # Linux/macOS
# or download from https://ollama.com/download/windows

# Pull a model
ollama pull qwen2.5-coder

### Installation

```bash
# Clone the repository
git clone https://github.com/medissaoui711/apex-core.git
cd apex-core

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build the resource database (one time only)
python copy_resources.py

# Run APEX
python apex.py
```

### First Run

When you first run APEX, you'll be prompted to select a provider:

```bash
🔌 جاري فحص مزودي الخدمة...

🔌 مزودي الخدمة المتاحين:

  1. 🏔️ Local (Ollama) (qwen2.5-coder)
  2. ⚡ Groq (Fast) (llama3-70b-8192)
  3. 🤖 OpenAI (gpt-3.5-turbo)

💡 الاقتراحات:
  • Local (Ollama) - Free, works offline
  • Groq - Very fast, free API tier

🔧 اختر رقم المزود (1-3): 1

```

## 📖 Commands Reference

### 🤖 Agents & Skills

| Command | Description | Example |
| ------- | ----------- | ------- |
| /agents | List all specialized agents | /agents |
| /agents python | Filter agents by language | /agents python |
| /skills | Skills summary | /skills |
| /skills all | List all skills (59) | /skills all |
| /skills categories | Show skill categories | /skills categories |
| /skills security | Search skills | /skills security |

### 🛠️ Development

| Command | Description | Example |
| ------- | ----------- | ------- |
| /plan | Create detailed development plan | /plan REST API with JWT |
| /code | Generate production-ready code | /code factorial function |
| /test | Generate comprehensive tests | /test sum function |
| /review | Code review with suggestions | /review app.py |
| /fix | Fix code issues | /fix bug.py |
| /build | Solve build problems | /build npm install fails |

### ☁️ Cloud Providers

| Command | Description | Example |
| ------- | ----------- | ------- |
| /provider | Show current provider | /provider |
| /provider groq | Switch to Groq | /provider groq |
| /providers | List available providers | /providers |

## 🔌 Providers

### 🏔️ Local (Ollama)

```bash
ollama pull qwen2.5-coder
ollama pull deepseek-coder-v2
ollama pull llama3
```

### ⚡ Groq (Fastest)

Get API key: console.groq.com

```bash
export GROQ_API_KEY="gsk_..."

```

### 🤖 OpenAI

Get API key: platform.openai.com

```bash
export OPENAI_API_KEY="sk-..."

```

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      APEX CLI (Rich UI)                     │
├─────────────────────────────────────────────────────────────┤
│                    Command Parser & Router                  │
├───────────────┬───────────────┬─────────────────────────────┤
│   /agents     │   /skills     │   /plan /code /test         │
│   /review     │   /fix        │   /build /file /shield      │
│   /provider   │   /providers  │   /learn /help /quit        │
├───────────────┴───────────────┴─────────────────────────────┤
│                    APEXCore (Orchestrator)                  │
├───────────────┬───────────────┬─────────────────────────────┤
│  load_agents  │  load_skills  │  load_rules  │  SQLite      │
├───────────────┴───────────────┴───────────────┴─────────────┤
│                     LLM Router (ask_llm)                     │
├───────────┬───────────┬───────────┬───────────┬─────────────┤
│  Ollama   │  OpenAI   │ Anthropic │  Gemini   │    Groq     │
│  (Local)  │  (Cloud)  │  (Cloud)  │  (Cloud)  │   (Cloud)   │
└───────────┴───────────┴───────────┴───────────┴─────────────┘
```

## 📁 Project Structure

```text
apex-core/
├── apex.py                 # Main application (601 lines)
├── copy_resources.py       # Resource extractor (538 lines)
├── requirements.txt        # Python dependencies
├── run_apex.bat           # Windows launcher
├── README.md              # Documentation
├── LICENSE                # License file
├── .gitignore             # Git ignore rules
└── .venv/                 # Virtual environment

~/.apex/                   # User data directory
├── apex.db                # SQLite database
├── agents/                # 47 specialized agents
├── skills/                # 59 categorized skills
├── rules/                 # 12 coding rules
├── shield/                # Security rules
├── instincts/             # Continuous learning
└── memory/                # Long-term memory
```

## 🗺️ Roadmap

### Version 1.2 (In Progress)

- Exponential backoff for API retries
- Rate limit handling (Groq, Together.ai)
- Conversation memory (multi-turn)
- Streaming responses

### Version 1.3 (Planned)

- VS Code extension
- Custom skill builder
- Project templates
- CI/CD integration

## 📄 License

Copyright © 2024 medissaoui711. All rights reserved.

This software is NOT open source. Commercial use requires a separate license.

| Use Case | License Required |
| -------- | ---------------- |
| Personal / Educational | ✅ Free |
| Commercial / SaaS | ❌ Requires commercial license |
| Redistribution | ❌ Prohibited |

For licensing inquiries: [GitHub Profile](https://github.com/medissaoui711)

## 🙏 Acknowledgements

- everything-claude-code - Resources and agents
- Ollama - Local LLM runner
- Rich - Beautiful terminal UI

---

Built with 🏔️ by [medissaoui711](https://github.com/medissaoui711) ·
[Report Bug](https://github.com/medissaoui711/apex-core/issues) ·
[Request Feature](https://github.com/medissaoui711/apex-core/issues)
