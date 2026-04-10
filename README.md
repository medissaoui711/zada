# 🏔️ APEX v1.1 - AI Programming Assistant

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Ollama](https://img.shields.io/badge/Ollama-Supported-orange.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Supported-412991.svg)
![Groq](https://img.shields.io/badge/Groq-Supported-FF6B00.svg)

**مساعد برمجي ذكي يجمع بين قوة النماذج المحلية (Local LLMs) والسحابية (Cloud APIs)**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Configuration](#configuration)
- [Providers](#providers)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**APEX** is a production-ready AI programming assistant that integrates:

- **Local LLMs** via Ollama (Qwen2.5-Coder, DeepSeek, Llama3, etc.)
- **Cloud APIs** (OpenAI, Anthropic, Google Gemini, Groq, Together.ai)
- **47 specialized agents** from the everything-claude-code ecosystem
- **59+ skills** covering security, testing, frontend, backend, and more

Built for developers who want **flexibility**, **privacy**, and **power** in their AI coding workflow.

---

## ✨ Features

### 🔌 Multi-Provider Support

| Provider | Model | Cost | Speed |
|----------|-------|------|-------|
| 🏔️ **Local (Ollama)** | Qwen2.5-Coder, DeepSeek, Llama3 | Free | Medium |
| 🤖 **OpenAI** | GPT-3.5/4 | Paid | Fast |
| 🧠 **Anthropic** | Claude 3 Sonnet | Paid | Medium |
| 🌐 **Google** | Gemini 1.5 Pro | Free (limited) | Fast |
| ⚡ **Groq** | Llama3 70B | Free | **Very Fast** |
| 🤝 **Together.ai** | Llama3 70B | Paid | Fast |

### 🎮 19 Powerful Commands

- **Agents:** `/agents`, `/agents python`, `/skills`, `/skills all`
- **Development:** `/plan`, `/code`, `/test`, `/review`, `/fix`, `/build`
- **Files:** `/file`, `/shield`, `/learn`
- **Cloud:** `/provider`, `/providers`

### 📦 Rich Resources

- **47 specialized agents** (Python, TypeScript, Go, Rust, Java, C++)
- **59 categorized skills** (Security, Testing, Frontend, Backend, DevOps)
- **12 coding rules** for best practices
- **SQLite database** for persistent storage

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APEX CLI (Rich UI)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Command Parser & Router                            │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│   /agents     │   /skills     │    /plan      │      /code /test            │
│   /review     │   /fix        │    /build     │      /file /shield          │
│   /provider   │   /providers  │    /learn     │      /help /quit            │
├───────────────┴───────────────┴───────────────┴─────────────────────────────┤
│                           APEXCore (Orchestrator)                           │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│  load_agents  │  load_skills  │  load_rules   │      SQLite / Files         │
├───────────────┴───────────────┴───────────────┴─────────────────────────────┤
│                           LLM Router (ask_llm)                              │
├───────────┬───────────┬───────────┬───────────┬───────────┬─────────────────┤
│  Ollama   │  OpenAI   │ Anthropic │  Gemini   │   Groq    │   Together      │
│  (Local)  │  (Cloud)  │  (Cloud)  │  (Cloud)  │  (Cloud)  │   (Cloud)       │
└───────────┴───────────┴───────────┴───────────┴───────────┴─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python 3.9+
python --version

# Install Ollama (for local models)
curl -fsSL https://ollama.com/install.sh | sh  # Linux/macOS
# or download from https://ollama.com/download/windows

# Pull a model (optional for local mode)
ollama pull qwen2.5-coder
```

### Installation

```bash
# Clone or download the project
cd C:\Users\DELL\Projects\ecl-core

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

When you first run APEX, you'll be prompted to:

1. **Select a provider** (Local, OpenAI, Groq, etc.)
2. **Choose a model** (if using local Ollama)

```
🔌 جاري فحص مزودي الخدمة...

🔌 مزودي الخدمة المتاحين:
  1. 🏔️ Local (Ollama) (qwen2.5-coder)
  2. ⚡ Groq (Fast) (llama3-70b-8192)
  3. 🤖 OpenAI (gpt-3.5-turbo)

💡 الاقتراحات:
  • Local (Ollama) - مجاني، يعمل بدون إنترنت
  • Groq - سريع جداً، يتطلب مفتاح API مجاني

🔧 اختر رقم المزود (1-3): 1
```

---

## 📖 Commands Reference

### 🤖 Agents & Skills

| Command | Description | Example |
|---------|-------------|---------|
| `/agents` | List all specialized agents | `/agents` |
| `/agents python` | Filter agents by language | `/agents python` |
| `/skills` | Skills summary | `/skills` |
| `/skills all` | List all skills (59) | `/skills all` |
| `/skills categories` | Show skill categories | `/skills categories` |
| `/skills security` | Search skills | `/skills security` |

### 🛠️ Development

| Command | Description | Example |
|---------|-------------|---------|
| `/plan` | Create detailed development plan | `/plan REST API with JWT` |
| `/code` | Generate production-ready code | `/code factorial function` |
| `/test` | Generate comprehensive tests | `/test sum function` |
| `/review` | Code review with suggestions | `/review app.py` |
| `/fix` | Fix code issues | `/fix bug.py` |
| `/build` | Solve build problems | `/build npm install fails` |

### 📁 Files & Security

| Command | Description | Example |
|---------|-------------|---------|
| `/file` | Read file content | `/file apex.py` |
| `/shield` | Security audit | `/shield` |
| `/learn` | Continuous learning report | `/learn` |

### ☁️ Cloud Providers

| Command | Description | Example |
|---------|-------------|---------|
| `/provider` | Show current provider | `/provider` |
| `/provider groq` | Switch to Groq | `/provider groq` |
| `/providers` | List available providers | `/providers` |

### ❓ Help

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/quit` | Exit APEX |

---

## ⚙️ Configuration

### Environment Variables (for Cloud APIs)

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Groq (free, fast inference)
export GROQ_API_KEY="gsk_..."

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GEMINI_API_KEY="AIza..."

# Together.ai
export TOGETHER_API_KEY="..."
```

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:GROQ_API_KEY = "gsk_..."
```

### Using `.env` File

```bash
# Create .env file
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

---

## 🔌 Providers

### 🏔️ Local (Ollama)

**Pros:** Free, private, works offline  
**Cons:** Slower, requires local storage

```bash
ollama pull qwen2.5-coder
ollama pull deepseek-coder-v2
ollama pull llama3
```

### ⚡ Groq

**Pros:** Very fast, free API tier  
**Cons:** Limited to specific models

Get API key: <https://console.groq.com>

### 🤖 OpenAI

**Pros:** Powerful models, excellent reasoning  
**Cons:** Paid, requires internet

Get API key: <https://platform.openai.com>

### 🧠 Anthropic Claude

**Pros:** Strong safety, long context  
**Cons:** Paid

Get API key: <https://console.anthropic.com>

### 🌐 Google Gemini

**Pros:** Free tier available, multimodal  
**Cons:** Limited rate

Get API key: <https://makersuite.google.com>

### 🤝 Together.ai

**Pros:** Many open models  
**Cons:** Paid

Get API key: <https://together.ai>

---

## 📁 Project Structure

```text
ecl-apex/
├── apex.py              # Main application (601 lines)
├── copy_resources.py    # Resource extractor (538 lines)
├── requirements.txt     # Python dependencies
├── run_apex.bat         # Windows launcher
└── .venv/              # Virtual environment

~/.apex/                 # User data directory
├── apex.db              # SQLite database
├── agents/              # 47 specialized agents
├── skills/              # 59 categorized skills
├── rules/               # 12 coding rules
├── hooks/               # Git hooks
├── examples/            # Code examples
├── templates/           # Project templates
├── shield/              # Security rules
├── instincts/           # Continuous learning
└── memory/              # Long-term memory
```

---

## 🔧 Technical Details

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ≥2.31.0 | HTTP API calls |
| `rich` | ≥13.7.0 | Beautiful CLI UI |
| `python-dotenv` | ≥1.0.0 | Environment variables |
| `colorama` | ≥0.4.6 | Terminal colors |

### Database Schema

```sql
-- Agents table
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    language TEXT,
    type TEXT,
    description TEXT,
    content TEXT,
    imported_at TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    category TEXT,
    level TEXT,
    description TEXT,
    imported_at TIMESTAMP
);

-- Rules table
CREATE TABLE rules (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    language TEXT,
    category TEXT,
    description TEXT,
    imported_at TIMESTAMP
);
```

---

## 🐛 Troubleshooting

### Ollama Connection Error

```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### Timeout Issues

```python
# Increase timeout in apex.py
timeout=600,  # Change from 300 to 600
```

### Missing API Keys

```bash
# Check environment variables
echo $OPENAI_API_KEY

# Or set them before running
export OPENAI_API_KEY="sk-..."
```

### Database Not Found

```bash
# Rebuild resources
python copy_resources.py
```

---

## 🗺️ Roadmap

### Version 1.2 (Planned)

- [ ] Exponential backoff for API retries
- [ ] Rate limit handling (Groq, Together.ai)
- [ ] Context injection (auto-rule selection)
- [ ] Conversation memory (multi-turn)

### Version 1.3 (Future)

- [ ] VS Code extension
- [ ] Autonomous agent mode
- [ ] Custom skill creation
- [ ] Project templates

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Development Setup

```bash
# Clone
git clone https://github.com/yourusername/apex.git
cd apex

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

---

## 📄 License

**MIT License** - Free for personal and commercial use.

---

## 🙏 Acknowledgements

- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) - Resources and agents
- [Ollama](https://ollama.com) - Local LLM runner
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal UI

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/medissaoui711)
- **Documentation:** See `docs/` folder
- **Email:** <contacteinfo71@gmail.com>

---

**Built with 🏔️ by Developers, for Developers**

[Report Bug](https://github.com/yourusername/apex/issues) · [Request Feature](https://github.com/yourusername/apex/issues)
