#!/usr/bin/env python3
"""
🏔️ ZADA v1.0 - Multi-Provider AI Coding Assistant
Where Code Grows
"""

import os
import subprocess
import sqlite3
import sys
import json
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

ZADA_HOME = Path.home() / ".zada"
DB_PATH = ZADA_HOME / "zada.db"
OLLAMA_MODEL = "qwen2.5-coder"

# ========== إعدادات Cloud APIs ==========
# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"

# Anthropic Claude
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"

# Google Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-pro"

# Groq (Fast Inference)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama3-70b-8192"

# Together.ai
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY", "")
TOGETHER_MODEL = "meta-llama/Llama-3-70b-chat-hf"

# ========== AgentShield - Security Layer ==========
import re
import time
from datetime import datetime
from typing import Tuple, List, Dict, Any

class AgentShield:
    """طبقة أمان متكاملة لحماية Zada من الأوامر الخطرة"""
    
    # قائمة الأوامر المسموح بها فقط (Whitelist)
    ALLOWED_COMMANDS = {
        'ls', 'dir', 'cat', 'type', 'echo', 'python', 'pip',
        'git', 'ollama', 'code', 'notepad', 'zada', 'apex'
    }
    
    # الملفات والمسارات الممنوعة
    FORBIDDEN_PATHS = {
        '/etc/passwd', '/etc/shadow', '/etc/hosts',
        '~/.ssh', '~/.aws', '~/.config',
        'C:\\Windows\\System32', 'C:\\Windows\\System',
        '/System', '/boot', '/dev', '/proc'
    }
    
    # الأنماط الممنوعة في الـ prompt (أكثر تحديداً)
    FORBIDDEN_PATTERNS = {
        'rm -rf /',           # حذف جذر النظام فقط
        'del /f /s',          # الحذف القسري الكامل
        'drop database',      # حذف قاعدة بيانات
        'truncate table',     # حذف جدول كامل
        'sudo rm',            # حذف بصلاحيات مدير
        'chmod 777 /',        # صلاحيات كاملة للجذر
    }
    
    # الأوامر التي تتطلب تأكيداً إضافياً
    DANGEROUS_COMMANDS = {
        'rm', 'del', 'rd', 'rmdir', 'move', 'rename',
        'shutdown', 'reboot', 'kill', 'taskkill'
    }
    
    def __init__(self):
        self.request_count = 0
        self.max_requests_per_minute = 30
        self.last_minute = 0
        self.audit_log = Path.home() / ".zada" / "audit.log"
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """التحقق من صحة الأمر"""
        if not command or not command.strip():
            return False, "Empty command"
        
        cmd_parts = command.strip().lower().split()
        base_cmd = cmd_parts[0]
        
        # فحص الأوامر المسموح بها
        if base_cmd not in self.ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' is not allowed"
        
        # فحص الأوامر الخطيرة (تتطلب تأكيداً)
        if base_cmd in self.DANGEROUS_COMMANDS:
            return True, f"DANGEROUS: Command '{base_cmd}' requires confirmation"
        
        return True, "OK"
    
    def validate_path(self, path: str) -> Tuple[bool, str]:
        """التحقق من صحة المسار"""
        try:
            resolved = str(Path(path).resolve()).lower()
            
            for forbidden in self.FORBIDDEN_PATHS:
                if forbidden.lower() in resolved:
                    return False, f"Access to '{forbidden}' is forbidden"
            
            return True, "OK"
        except Exception as e:
            return False, f"Invalid path: {str(e)}"
    
    def validate_prompt(self, prompt: str, is_system_prompt: bool = False) -> tuple[bool, str]:
        """التحقق من صحة الـ prompt (منع الحقن)"""
        if not prompt:
            return True, "OK"

        # إذا كان System Prompt، خفف الفحص
        if is_system_prompt:
            # فقط افحص الأنماط الخطيرة جداً
            critical_patterns = ['rm -rf /', 'drop database', 'truncate table', 'sudo rm']
            for pattern in critical_patterns:
                if pattern in prompt.lower():
                    return False, f"Critical pattern '{pattern}' is forbidden"
            return True, "OK"

        # الفحص العادي
        prompt_lower = prompt.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(re.escape(pattern), prompt_lower):
                return False, f"Pattern '{pattern}' is forbidden"
        if len(prompt) > 10000:
            return False, "Prompt too long (max 10000 characters)"
        return True, "OK"

    def validate_prompt_advanced(self, prompt: str, client_id: str = "default", is_system_prompt: bool = False) -> tuple[bool, str]:
        """Advanced multi-layer prompt validation"""

        # If this is a System Prompt (from prompts folder), relax the check
        if is_system_prompt:
            # Only check for very dangerous patterns
            critical_patterns = [
                r"ignore.*instructions",
                r"bypass.*security",
                r"override.*system",
                r"sudo\s+rm\s+-rf",  # Only dangerous rm -rf
            ]
            for pattern in critical_patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    self.audit("SYSTEM_PROMPT_BLOCKED", {"reason": pattern, "client": client_id}, "CRITICAL")
                    return False, "System prompt contains dangerous pattern"
            return True, prompt

        # Normal check (for regular users)
        # Use existing validate_prompt for standard validation
        valid, msg = self.validate_prompt(prompt)
        if not valid:
            return False, msg

        return True, prompt

    def check_rate_limit(self) -> Tuple[bool, str]:
        """التحقق من معدل الطلبات"""
        current_minute = int(time.time() / 60)
        
        if current_minute != self.last_minute:
            self.last_minute = current_minute
            self.request_count = 0
        
        self.request_count += 1
        
        if self.request_count > self.max_requests_per_minute:
            return False, f"Rate limit exceeded ({self.max_requests_per_minute} requests/minute)"
        
        return True, "OK"
    
    def audit(self, action: str, details: Dict[str, Any], level: str = "INFO"):
        """تسجيل الأحداث الأمنية"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "action": action,
            "details": details
        }
        
        try:
            with open(self.audit_log, "a", encoding='utf-8') as f:
                f.write(f"{audit_entry}\n")
        except Exception:
            pass
        
        # عرض تحذير للمستخدم
        if level == "WARNING":
            from rich.console import Console
            console = Console()
            console.print(f"[yellow]⚠️ Security: {action} - {details.get('reason', '')}[/yellow]")
        elif level == "CRITICAL":
            from rich.console import Console
            console = Console()
            console.print(f"[red]🔒 CRITICAL: {action} - {details.get('reason', '')}[/red]")
    
    def get_audit_log(self, limit: int = 20) -> List[Dict]:
        """استرجاع سجل الأمان"""
        logs = []
        if not self.audit_log.exists():
            return logs
        
        try:
            with open(self.audit_log, "r", encoding='utf-8') as f:
                for line in f:
                    try:
                        logs.append(eval(line))
                    except:
                        pass
        except Exception:
            pass
        
        return logs[-limit:]
    
    def get_stats(self) -> Dict:
        """إحصائيات الأمان"""
        logs = self.get_audit_log(1000)
        
        stats = {
            "total_requests": len(logs),
            "blocked": len([l for l in logs if l.get("level") in ["WARNING", "CRITICAL"]]),
            "by_action": {}
        }
        
        for log in logs:
            action = log.get("action", "unknown")
            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
        
        return stats


class ZadaCore:
    zada_home: Path
    db_path: Path
    current_workspace: Path
    conversation_history: list[dict[str, Any]]
    current_provider: str
    agents: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    rules: list[dict[str, Any]]

    def __init__(self) -> None:
        self.zada_home = ZADA_HOME
        self.db_path = DB_PATH
        self.current_workspace = Path.cwd()
        self.conversation_history: list[dict[str, Any]] = []
        
        # Select provider
        console.print("\n[bold cyan]🔌 Checking available providers...[/bold cyan]")
        self.current_provider = self.select_provider_interactive()
        console.print(f"[green]✅ Provider selected: {self.current_provider}[/green]")
        
        # Load resources
        self.agents = self.load_agents()
        self.skills = self.load_skills()
        self.rules = self.load_rules()
        
        # Add AgentShield
        self.shield = AgentShield()
        
        console.print(f"[green]✅ ZADA initialized with AgentShield[/green]")
        console.print(f"[dim]📊 Agents: {len(self.agents)} | Skills: {len(self.skills)} | Rules: {len(self.rules)}[/dim]")
    
    def load_agents(self) -> list[dict[str, Any]]:
        agents: list[dict[str, Any]] = []
        try:
            if not self.db_path.exists():
                return agents
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            _ = cursor.execute("SELECT name, language, type, description FROM agents")
            rows = cursor.fetchall()
            for row in rows:
                agents.append({
                    "name": row[0] if row[0] else "unknown",
                    "language": row[1] if row[1] else "general",
                    "type": row[2] if row[2] else "general",
                    "description": row[3][:150] if row[3] else ""
                })
            conn.close()
            console.print(f"[dim]📚 Loaded {len(agents)} agents[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Agents error: {e}[/yellow]")
        return agents
    
    def load_skills(self) -> list[dict[str, Any]]:
        """Load all skills from the skills directory directly"""
        skills: list[dict[str, Any]] = []
        skills_dir = self.zada_home / "skills"

        if skills_dir.exists():
            for category_dir in skills_dir.glob("*"):
                if category_dir.is_dir():
                    for skill_file in category_dir.glob("*.md"):
                        if skill_file.name.endswith('.metadata.json'):
                            continue

                        # Read description from metadata file if found
                        description = ""
                        json_file = category_dir / f"{skill_file.stem}.metadata.json"
                        if json_file.exists():
                            try:
                                data = json.loads(json_file.read_text(encoding='utf-8'))
                                description = data.get("description", "")[:150]
                            except:
                                pass

                        skills.append({
                            "name": skill_file.stem,
                            "category": category_dir.name,
                            "level": "intermediate",
                            "description": description
                        })

        console.print(f"[dim]📚 Loaded {len(skills)} skills from folders[/dim]")
        return skills
    
    def load_rules(self) -> list[dict[str, Any]]:
        rules: list[dict[str, Any]] = []
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                _ = cursor.execute("SELECT name, language, category, description FROM rules")
                rows = cursor.fetchall()
                for row in rows:
                    rules.append({
                        "name": row[0] if row[0] else "unknown",
                        "language": row[1] if row[1] else "general",
                        "category": row[2] if row[2] else "general",
                        "description": row[3][:150] if row[3] else ""
                    })
                conn.close()
        except Exception as e:
            console.print(f"[yellow]⚠️ Rules error: {e}[/yellow]")
        return rules
    
    def ask_ollama(self, prompt: str) -> str:
        """Send request to LLM (supports Local and Cloud)"""
        return self.ask_llm(prompt, "local")

    # ========== Cloud APIs ==========
    def ask_openai(self, prompt: str) -> str:
        """Send request to OpenAI API"""
        if not OPENAI_API_KEY:
            return "❌ OpenAI API key not found. Please set OPENAI_API_KEY in environment variables"
        try:
            import requests
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 4096
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"❌ OpenAI Error: {response.status_code}"
        except Exception as e:
            return f"❌ OpenAI Error: {str(e)}"

    def ask_anthropic(self, prompt: str) -> str:
        """Send request to Anthropic Claude API"""
        if not ANTHROPIC_API_KEY:
            return "❌ Anthropic API key not found"
        try:
            import requests
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                    "temperature": 0.4
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            return f"❌ Anthropic Error: {response.status_code}"
        except Exception as e:
            return f"❌ Anthropic Error: {str(e)}"

    def ask_gemini(self, prompt: str) -> str:
        """Send request to Google Gemini API"""
        if not GEMINI_API_KEY:
            return "❌ Gemini API key not found"
        try:
            import requests
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return f"❌ Gemini Error: {response.status_code}"
        except Exception as e:
            return f"❌ Gemini Error: {str(e)}"

    def ask_groq(self, prompt: str) -> str:
        """Send request to Groq API (very fast)"""
        if not GROQ_API_KEY:
            return "❌ Groq API key not found"
        try:
            import requests
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 4096
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"❌ Groq Error: {response.status_code}"
        except Exception as e:
            return f"❌ Groq Error: {str(e)}"

    def ask_together(self, prompt: str) -> str:
        """Send request to Together.ai API"""
        if not TOGETHER_API_KEY:
            return "❌ Together.ai API key not found"
        try:
            import requests
            response = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": TOGETHER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 4096
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return f"❌ Together.ai Error: {response.status_code}"
        except Exception as e:
            return f"❌ Together.ai Error: {str(e)}"

    # ========== Manage Resources (Local / Cloud) ==========
    def get_available_providers(self) -> list[dict[str, Any]]:
        """Get the list of available providers"""
        providers: list[dict[str, Any]] = [
            {"name": "local", "display": "🏔️ Local (Ollama)", "model": OLLAMA_MODEL, "available": True}
        ]
        if OPENAI_API_KEY:
            providers.append({"name": "openai", "display": "🤖 OpenAI", "model": OPENAI_MODEL, "available": True})
        if ANTHROPIC_API_KEY:
            providers.append({"name": "anthropic", "display": "🧠 Anthropic Claude", "model": ANTHROPIC_MODEL, "available": True})
        if GEMINI_API_KEY:
            providers.append({"name": "gemini", "display": "🌐 Google Gemini", "model": GEMINI_MODEL, "available": True})
        if GROQ_API_KEY:
            providers.append({"name": "groq", "display": "⚡ Groq (Fast)", "model": GROQ_MODEL, "available": True})
        if TOGETHER_API_KEY:
            providers.append({"name": "together", "display": "🤝 Together.ai", "model": TOGETHER_MODEL, "available": True})
        return providers

    def select_provider_interactive(self) -> str:
        """Display available providers and request selection"""
        providers = self.get_available_providers()
        console.print("\n[bold cyan]🔌 Available Providers:[/bold cyan]")
        for i, p in enumerate(providers, 1):
            console.print(f"  {i}. {p['display']} [dim]({p['model']})[/dim]")
        console.print("\n[bold yellow]💡 Suggestions:[/bold yellow]")
        console.print("  • [green]Local (Ollama)[/green] - Free, works offline")
        console.print("  • [green]Groq[/green] - Very fast, free API key required")
        console.print("  • [green]OpenAI[/green] - Powerful, requires subscription")
        while True:
            try:
                choice = console.input(f"\n[bold cyan]🔧 Choose provider number (1-{len(providers)}): [/bold cyan]").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(providers):
                        selected = providers[idx]["name"]
                        console.print(f"[green]✅ Selected: {providers[idx]['display']}[/green]")
                        return selected
                    console.print(f"[red]❌ Invalid number. Choose from 1 to {len(providers)}[/red]")
                else:
                    console.print("[red]❌ Please enter a valid number[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Cancelled, using Local[/yellow]")
                return "local"

    def ask_llm(self, prompt: str, provider: str = None) -> str:
        """Send request with security check"""
        
        # 1. Validate prompt
        valid, msg = self.shield.validate_prompt(prompt)
        if not valid:
            self.shield.audit("BLOCKED_PROMPT", {"prompt": prompt[:100], "reason": msg}, "WARNING")
            return f"🔒 Security: {msg}"
        
        # 2. Check rate limit
        valid, msg = self.shield.check_rate_limit()
        if not valid:
            return f"🔒 Security: {msg}"
        
        # 3. Log request
        provider = provider or getattr(self, 'current_provider', 'local')
        self.shield.audit("LLM_REQUEST", {"provider": provider, "prompt_len": len(prompt)})
        
        # 4. Execute original request
        if provider == "local":
            try:
                console.print("[dim]⏳ Connecting to Ollama...[/dim]")
                result = subprocess.run(
                    ["ollama", "run", OLLAMA_MODEL, prompt],
                    capture_output=True, text=True, timeout=300, encoding='utf-8'
                )
                return result.stdout.strip() if result.returncode == 0 else f"❌ Error: {result.stderr}"
            except subprocess.TimeoutExpired:
                return "❌ Timeout: Request took too long"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        elif provider == "openai":
            return self.ask_openai(prompt)
        elif provider == "anthropic":
            return self.ask_anthropic(prompt)
        elif provider == "gemini":
            return self.ask_gemini(prompt)
        elif provider == "groq":
            return self.ask_groq(prompt)
        elif provider == "together":
            return self.ask_together(prompt)
        return f"❌ Unknown provider: {provider}"

    def cmd_agents(self, args: str = "") -> str:
        if args:
            agents = [a for a in self.agents if args.lower() in a["language"].lower() or args.lower() in a["name"].lower()]
            if not agents:
                return f"❌ No agents found for language: {args}"
            result = f"## 🤖 Agents for {args.upper()}\n\n"
            for a in agents[:20]:
                result += f"- **{a['name']}** ({a['type']})\n  - {a['description'][:80]}...\n\n"
            return result
        
        result = "## 🤖 All Agents\n\n"
        by_lang = {}
        for a in self.agents:
            by_lang.setdefault(a["language"], []).append(a["name"])
        for lang, names in sorted(by_lang.items()):
            result += f"### {lang.upper()} ({len(names)})\n"
            result += ", ".join(names[:15])
            if len(names) > 15:
                result += f" ... and {len(names)-15} more"
            result += "\n\n"
        return result
    
    def cmd_skills(self, args: str = "") -> str:
        if not self.skills:
            return "⚠️ No skills found. Please run copy_resources.py"
        
        if args == "all":
            result = f"## 🛠️ All Skills ({len(self.skills)})\n\n"
            by_cat = {}
            for s in self.skills:
                by_cat.setdefault(s["category"], []).append(s["name"])
            for cat, names in sorted(by_cat.items()):
                result += f"### {cat.upper()} ({len(names)})\n"
                for name in names[:20]:
                    result += f"- {name}\n"
                if len(names) > 20:
                    result += f"- ... and {len(names)-20} more\n"
                result += "\n"
            return result
        
        if args == "categories":
            cats = {}
            for s in self.skills:
                cats[s["category"]] = cats.get(s["category"], 0) + 1
            result = "## 🛠️ Skill Categories\n\n"
            for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
                result += f"- **{cat.upper()}**: {count} skills\n"
            return result
        
        if args:
            matches = [s for s in self.skills if args.lower() in s["name"].lower() or args.lower() in s["description"].lower()]
            if not matches:
                return f"❌ No skills found matching: {args}"
            result = f"## 🛠️ Search Results: {args}\n\n"
            for s in matches[:15]:
                result += f"- **{s['name']}** ({s['category']})\n  - {s['description'][:80]}...\n\n"
            return result
        
        result = "## 🛠️ Skill Summary\n\n"
        cats = {}
        for s in self.skills:
            cats[s["category"]] = cats.get(s["category"], 0) + 1
        for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10]:
            result += f"- **{cat.upper()}**: {count} skills\n"
        result += f"\n📊 **Total Skills: {len(self.skills)}**\n"
        result += "\n💡 Use:\n"
        result += "   - `/skills all` - to view all skills\n"
        result += "   - `/skills categories` - to view categories\n"
        result += "   - `/skills <word>` - to search\n"
        return result
    
    def cmd_plan(self, args: str) -> str:
        if not args:
            return "❌ Please describe the task"
        # Shorter and faster formulation
        return self.ask_ollama(f"Plan for: {args}")
    
    def cmd_code(self, args: str) -> str:
        if not args:
            return "❌ Please describe the code needed"
        # Shorter and faster formulation
        return self.ask_ollama(f"Write code for: {args}")
    
    def cmd_test(self, args: str) -> str:
        if not args:
            return "❌ Please describe the component"
        # Shorter and faster formulation
        return self.ask_ollama(f"Write tests for: {args}")
    
    def cmd_file(self, args: str) -> str:
        if not args:
            return "❌ Please specify a file path"
        p = Path(args)
        if not p.is_absolute():
            p = self.current_workspace / args
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding='utf-8')
                return f"## 📄 {p.name}\n\n```\n{content[:2000]}\n```"
            except Exception as e:
                return f"❌ Error: {e}"
        return f"❌ File not found: {args}"
    
    def cmd_shield(self, args: str = "") -> str:
        """Display security report"""
        stats = self.shield.get_stats()
        
        return f"""
## 🛡️ AgentShield Report

| Metric | Value |
|---------|--------|
| Total Requests | {stats['total_requests']} |
| Blocked Requests | {stats['blocked']} |
| Requests/Minute | {self.shield.max_requests_per_minute} |

### Events by Type
{chr(10).join([f"- {k}: {v}" for k, v in stats['by_action'].items()])}

💡 View details: `/audit` 
"""

    def cmd_audit(self, args: str = "") -> str:
        """Display security log"""
        logs = self.shield.get_audit_log(20)
        
        if not logs:
            return "📭 No security events logged"
        
        result = "## 🔒 Audit Log (last 20 events)\n\n"
        for log in reversed(logs):
            level_icon = "🔴" if log.get("level") == "CRITICAL" else "🟡" if log.get("level") == "WARNING" else "🔵"
            result += f"{level_icon} **{log['timestamp']}** - {log['action']}\n"
            if log.get('details'):
                result += f"   └─ {log['details']}\n"
            result += "\n"
        
        return result

    def cmd_learn(self, args: str = "") -> str:
        return "📊 Continuous Learning: 0 sessions recorded so far"
    
    def cmd_review(self, args: str) -> str:
        if not args:
            return "❌ Please specify a file for review"
        file_path = Path(args)
        if not file_path.is_absolute():
            file_path = self.current_workspace / args
        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding='utf-8')[:3000]
            return self.ask_ollama(f"Please review this code carefully:\n\n{content}")
        return f"❌ File not found: {args}"

    def cmd_fix(self, args: str) -> str:
        if not args:
            return "❌ Please specify a file to fix"
        file_path = Path(args)
        if not file_path.is_absolute():
            file_path = self.current_workspace / args
        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding='utf-8')[:3000]
            return self.ask_ollama(f"Please analyze and fix issues in this code:\n\n{content}")
        return f"❌ File not found: {args}"

    def cmd_build(self, args: str) -> str:
        if not args:
            return "❌ Please describe the build issue"
        return self.ask_ollama(f"Please analyze the build issue and suggest a solution:\n\n{args}")

    def cmd_provider(self, args: str) -> str:
        """Change the provider"""
        if not args:
            return f"🔌 Current provider: {self.current_provider}\n\nUse `/provider <name>` to change the provider\nAvailable names: local, openai, anthropic, gemini, groq, together"
        providers = [p["name"] for p in self.get_available_providers()]
        if args in providers:
            self.current_provider = args
            return f"✅ Provider changed to: {args}"
        return f"❌ Provider '{args}' not available.\n\nAvailable providers:\n" + "\n".join(f"  • {p}" for p in providers)

    def cmd_providers(self) -> str:
        """Display all available providers"""
        providers = self.get_available_providers()
        result = "## 🔌 Available Providers\n\n"
        for p in providers:
            current = " ✅ (Current)" if p["name"] == self.current_provider else ""
            result += f"- **{p['display']}**{current}\n"
            result += f"  - Model: `{p['model']}`\n\n"
        return result

    # ========== Prompt Agents Management ==========

    def get_prompt_agents(self) -> list[str]:
        """Get list of imported agents from prompts folder"""
        prompts_dir = self.zada_home / "prompts"
        if not prompts_dir.exists():
            return []
        return [p.stem for p in prompts_dir.glob("*.md")]

    def load_agent_prompt(self, agent_name: str) -> str:
        """Load system prompt for a specific agent"""
        prompt_path = self.zada_home / "prompts" / f"{agent_name}.md"
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""

    def cmd_use_agent(self, args: str) -> str:
        """Use a custom agent from prompts folder"""
        if not args:
            agents = self.get_prompt_agents()
            if not agents:
                return "⚠️ No prompt agents found. Run 'python copy_prompts.py' first."

            result = f"## 🤖 Available Prompt Agents ({len(agents)})\n\n"
            # Display first 30 agents
            for agent in agents[:30]:
                result += f"- `{agent}`\n"
            if len(agents) > 30:
                result += f"\n... and {len(agents) - 30} more\n"
            result += f"\n💡 Usage: `/use-agent <agent-name> <prompt>`\n"
            result += f"📁 Location: `{self.zada_home / 'prompts'}`"
            return result

        parts = args.split(maxsplit=1)
        agent_name = parts[0]
        user_prompt = parts[1] if len(parts) > 1 else ""

        if not user_prompt:
            return f"❌ Please provide a prompt. Example: `/use-agent {agent_name} 'Write code'`"

        system_prompt = self.load_agent_prompt(agent_name)
        if not system_prompt:
            agents = self.get_prompt_agents()
            return f"❌ Agent '{agent_name}' not found.\n\nAvailable: {', '.join(agents[:10])}..."

        # Combine system prompt with user prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Pass is_system_prompt=True to relax security check
        valid, msg = self.shield.validate_prompt(full_prompt, is_system_prompt=True)
        if not valid:
            return f"🔒 Security: {msg}"

        return self.ask_ollama(full_prompt)

    def cmd_help(self) -> str:
        return """
## 🏔️ ZADA v1.0 - Multi-Provider AI Coding Assistant

| Command | Description | Example |
|-------|-------|------|
| `/agents` | Display all agents | `/agents` |
| `/agents <lang>` | Agents for a specific language | `/agents python` |
| `/skills` | Skill summary | `/skills` |
| `/skills all` | Display all skills | `/skills all` |
| `/skills categories` | Display skill categories | `/skills categories` |
| `/skills <word>` | Search skills | `/skills security` |
| `/plan <desc>` | Plan for a task | `/plan website` |
| `/code <desc>` | Write code for a task | `/code sum function` |
| `/test <desc>` | Write tests for a component | `/test sum function` |
| `/file <path>` | Read a file | `/file zada.py` |
| `/shield` | Display security report | `/shield` |
| `/audit` | Display security log | `/audit` |
| `/learn` | Continuous learning | `/learn` |
| `/review <path>` | Review a file | `/review file.py` |
| `/fix <path>` | Fix a file | `/fix file.py` |
| `/build <desc>` | Solve a build issue | `/build build error` |
| `/provider [name]` | Display/change provider | `/provider groq` |
| `/providers` | Display all providers | `/providers` |
| `/use-agent [name] [prompt]` | Use a prompt agent | `/use-agent zada-3.1-pro "Write code"` |
| `/help` | Help | `/help` |
| `/quit` | Quit | `/quit` |
"""
    
    def handle_command(self, cmd: str, args: str) -> str:
        if cmd == "agents":
            return self.cmd_agents(args)
        elif cmd == "skills":
            return self.cmd_skills(args)
        elif cmd == "plan":
            return self.cmd_plan(args)
        elif cmd == "code":
            return self.cmd_code(args)
        elif cmd == "test":
            return self.cmd_test(args)
        elif cmd == "file":
            return self.cmd_file(args)
        elif cmd == "shield":
            return self.cmd_shield(args)
        elif cmd == "audit":
            return self.cmd_audit(args)
        elif cmd == "learn":
            return self.cmd_learn(args)
        elif cmd == "review":
            return self.cmd_review(args)
        elif cmd == "fix":
            return self.cmd_fix(args)
        elif cmd == "build":
            return self.cmd_build(args)
        elif cmd == "provider":
            return self.cmd_provider(args)
        elif cmd == "providers":
            return self.cmd_providers()
        elif cmd == "use-agent":
            return self.cmd_use_agent(args)
        elif cmd == "help":
            return self.cmd_help()
        else:
            return f"❌ Unknown command: {cmd}\n{self.cmd_help()}"
    
    def run(self):
        """Run ZADA CLI"""

        # ASCII Art Logo for CLI
        logo = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗ █████╗ ██████╗  █████╗     ███████╗ █████╗ ██████╗  █████╗        ║
║   ╚══███╔╝██╔══██╗██╔══██╗██╔══██╗    ╚══███╔╝██╔══██╗██╔══██╗██╔══██║       ║
║     ███╔╝ ███████║██║  ██║███████║      ███╔╝ ███████║██║  ██║███████║       ║
║    ███╔╝  ██╔══██║██║  ██║██╔══██║     ███╔╝  ██╔══██║██║  ██║██╔══██║       ║
║   ███████╗██║  ██║██████╔╝██║  ██║    ███████╗██║  ██║██████╔╝██║  ██║       ║
║   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝       ║
║                                                                              ║
║   ┌─────────────────────────────────────────────────────────────────────────┐║
║   │  $ python zada.py                                                       │║
║   │  ✅ ZADA v1.0 initialized                                              │║
║   │  📊 Agents: 47 | Skills: 19 | Rules: 12                                │║
║   │  🏔️ ZADA ready! Type /help to see all commands                        │║
║   └─────────────────────────────────────────────────────────────────────────┘║
║                                                                              ║
║   Where Code Grows                                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        console.print(logo, style="cyan")

        console.print(Panel.fit(
            "[bold cyan]🏔️ ZADA v1.0 - Multi-Provider AI Coding Assistant[/bold cyan]\n"
            f"[yellow]📁 Workspace: {self.current_workspace}[/yellow]",
            border_style="cyan"
        ))
        console.print(f"\n[green]✅ ZADA ready! {len(self.agents)} agents, {len(self.skills)} skills[/green]\n")
        console.print("[dim]💡 Type /help to see all commands[/dim]\n")
        
        while True:
            try:
                user = console.input("[bold cyan]🏔️ ZADA>[/bold cyan] ").strip()
                if not user:
                    continue
                if user.lower() in ["/quit", "exit", "quit"]:
                    console.print("[yellow]👋 Goodbye! ZADA is waiting for your return.[/yellow]")
                    break
                if user.startswith("/"):
                    parts = user.split(maxsplit=1)
                    cmd = parts[0][1:].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as p:
                        p.add_task("Processing...", total=None)
                        result = self.handle_command(cmd, args)
                    console.print("\n[bold cyan]💡 Response:[/bold cyan]\n")
                    console.print(Markdown(result))
                    console.print("\n" + "="*60)
                else:
                    result = self.ask_ollama(user)
                    console.print("\n[bold cyan]💡 Response:[/bold cyan]\n")
                    console.print(Markdown(result))
                    console.print("\n" + "="*60)
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Exiting...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    if not DB_PATH.exists():
        console.print("[red]❌ Database not found! Run copy_resources.py first[/red]")
        sys.exit(1)
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        console.print("[green]✅ Ollama connected[/green]")
    except:
        console.print("[yellow]⚠️ Ollama not found[/yellow]")
    zada = ZadaCore()
    zada.run()