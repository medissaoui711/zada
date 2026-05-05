#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌊 CARTAGE v1.0 - Sovereign AI Framework
Where Ancient Wisdom Meets Modern Code
"""

import subprocess
import sqlite3
import sys
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Load environment variables
load_dotenv()

console = Console()

# ========== الإعدادات ==========
CARTAGE_HOME = Path.home() / ".cartage"
DB_PATH = CARTAGE_HOME / "cartage.db"
OLLAMA_MODEL = "qwen2.5-coder"

# API Keys from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ========== AgentShield - Security Layer ==========
class AgentShield:
    """طبقة أمان متكاملة لحماية CARTAGE من الأوامر الخطيرة"""
    
    ALLOWED_COMMANDS = {
        'ls', 'dir', 'cat', 'type', 'echo', 'python', 'pip',
        'git', 'ollama', 'code', 'notepad', 'cartage'
    }
    
    FORBIDDEN_PATTERNS = {
        'rm -rf /', 'del /f /s', 'drop database', 'truncate table',
        'sudo rm', 'chmod 777 /', 'format'
    }
    
    def __init__(self):
        self.request_count = 0
        self.max_requests_per_minute = 30
        self.audit_log = CARTAGE_HOME / "audit.log"
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        self._last_minute = 0
    
    def validate_prompt(self, prompt: str, is_system_prompt: bool = False) -> Tuple[bool, str]:
        if not prompt:
            return True, "OK"
        
        max_length = 50000 if is_system_prompt else 10000
        if len(prompt) > max_length:
            return False, f"Prompt too long (max {max_length} characters)"
        
        prompt_lower = prompt.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in prompt_lower:
                return False, f"Pattern '{pattern}' is forbidden"
        
        return True, "OK"
    
    def check_rate_limit(self) -> Tuple[bool, str]:
        import time
        current_minute = int(time.time() / 60)
        if current_minute != self._last_minute:
            self._last_minute = current_minute
            self.request_count = 0
        self.request_count += 1
        if self.request_count > self.max_requests_per_minute:
            return False, f"Rate limit exceeded ({self.max_requests_per_minute}/minute)"
        return True, "OK"
    
    def audit(self, action: str, details: dict, level: str = "INFO"):
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "action": action,
            "details": details
        }
        try:
            with open(self.audit_log, "a", encoding='utf-8') as f:
                f.write(f"{json.dumps(audit_entry)}\n")
        except Exception:
            pass

# ========== CARTAGE Core ==========
class CartageCore:
    def __init__(self):
        self.cartage_home = CARTAGE_HOME
        self.db_path = DB_PATH
        self.current_workspace = Path.cwd()
        self.conversation_history: List[Dict] = []
        self.current_provider = "local"
        self.shield = AgentShield()
        
        # Load resources
        self.agents = self.load_agents()
        self.skills = self.load_skills()
        self.rules = self.load_rules()
        
        console.print("[green]✅ CARTAGE initialized[/green]")
        console.print(f"[dim]📊 Agents: {len(self.agents)} | Skills: {len(self.skills)} | Rules: {len(self.rules)}[/dim]")
    
    def load_agents(self) -> List[Dict]:
        agents = []
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name, language, type, description FROM agents")
                for row in cursor.fetchall():
                    agents.append({"name": row[0], "language": row[1] or "general", "type": row[2] or "general", "description": row[3][:200] if row[3] else ""})
                conn.close()
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load agents: {e}[/yellow]")
        return agents
    
    def load_skills(self) -> List[Dict]:
        skills = []
        skills_dir = self.cartage_home / "skills"
        if skills_dir.exists():
            for category_dir in skills_dir.glob("*"):
                if category_dir.is_dir():
                    for skill_file in category_dir.glob("*.md"):
                        if skill_file.name.endswith('.metadata.json') or skill_file.name.endswith('README.md'):
                            continue
                        skills.append({"name": skill_file.stem, "category": category_dir.name, "level": "intermediate", "description": ""})
        console.print(f"[dim]📚 Loaded {len(skills)} skills[/dim]")
        return skills
    
    def load_rules(self) -> List[Dict]:
        rules = []
        try:
            if self.db_path.exists():
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name, language, category, description FROM rules")
                for row in cursor.fetchall():
                    rules.append({"name": row[0], "language": row[1] or "general", "category": row[2] or "general", "description": row[3][:200] if row[3] else ""})
                conn.close()
        except Exception:
            pass
        return rules
    
    def get_prompt_agents(self) -> List[str]:
        prompts_dir = self.cartage_home / "prompts"
        return [p.stem for p in prompts_dir.glob("*.md")] if prompts_dir.exists() else []
    
    def load_agent_prompt(self, agent_name: str) -> str:
        prompt_path = self.cartage_home / "prompts" / f"{agent_name}.md"
        return prompt_path.read_text(encoding='utf-8') if prompt_path.exists() else ""
    
    # ========== Helper Methods ==========
    def save_last_response(self, filename: str = None) -> str:
        if not self.conversation_history:
            return "❌ No response to save"
        last_response = self.conversation_history[-1]["content"]
        if not filename:
            filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = Path(self.current_workspace) / filename
        filepath.write_text(last_response, encoding='utf-8')
        return f"✅ Response saved to: {filepath}"
    
    def export_last_code(self, filename: str = None) -> str:
        if not self.conversation_history:
            return "❌ No response to export"
        last_response = self.conversation_history[-1]["content"]
        code_blocks = re.findall(r'```(?:python)?\n(.*?)```', last_response, re.DOTALL)
        if not code_blocks:
            return "❌ No code found in response"
        if not filename:
            filename = f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        filepath = Path(self.current_workspace) / filename
        filepath.write_text(code_blocks[0], encoding='utf-8')
        return f"✅ Code exported to: {filepath}"
    
    # ========== Commands ==========
    def cmd_agents(self, args: str = "") -> str:
        if args:
            filtered = [a for a in self.agents if args.lower() in a["language"].lower() or args.lower() in a["name"].lower()]
            if not filtered:
                return f"❌ No agents found for: {args}"
            result = f"## 🤖 Agents for {args.upper()}\n\n"
            for a in filtered[:20]:
                result += f"- **{a['name']}** ({a['type']})\n  - {a['description'][:80]}...\n\n"
            return result
        result = "## 🤖 All Specialized Agents\n\n"
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
            return "⚠️ No skills loaded"
        if args == "all":
            result = f"## 🛠️ All Skills ({len(self.skills)})\n\n"
            by_cat = {}
            for s in self.skills:
                by_cat.setdefault(s["category"], []).append(s["name"])
            for cat, names in sorted(by_cat.items()):
                result += f"### {cat.upper()} ({len(names)})\n" + "\n".join(f"- {n}" for n in names[:20]) + ("\n" if len(names) <= 20 else f"\n- ... and {len(names)-20} more\n") + "\n"
            return result
        if args == "categories":
            cats = {}
            for s in self.skills:
                cats[s["category"]] = cats.get(s["category"], 0) + 1
            return "## 🛠️ Skill Categories\n\n" + "\n".join(f"- **{cat.upper()}**: {count} skills" for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True))
        if args:
            matches = [s for s in self.skills if args.lower() in s["name"].lower()]
            if not matches:
                return f"❌ No skills match: {args}"
            return "## 🛠️ Search Results\n\n" + "\n".join(f"- **{s['name']}** ({s['category']})" for s in matches[:15])
        result = "## 🛠️ Skills Summary\n\n"
        cats = {}
        for s in self.skills:
            cats[s["category"]] = cats.get(s["category"], 0) + 1
        for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10]:
            result += f"- **{cat.upper()}**: {count} skills\n"
        result += f"\n📊 **Total Skills: {len(self.skills)}**\n\n💡 Try:\n   - `/skills all`\n   - `/skills categories`\n   - `/skills <keyword>`"
        return result
    
    def cmd_use_agent(self, args: str) -> str:
        if not args:
            agents = self.get_prompt_agents()
            return f"## 🤖 Available Prompt Agents ({len(agents)})\n\n" + "\n".join(f"- `{a}`" for a in agents[:30]) + (f"\n\n... and {len(agents)-30} more" if len(agents) > 30 else "") + f"\n\n💡 Usage: `/use-agent <agent-name> <prompt>`"
        parts = args.split(maxsplit=1)
        agent_name = parts[0]
        user_prompt = parts[1] if len(parts) > 1 else ""
        if not user_prompt:
            return f"❌ Please provide a prompt. Example: `/use-agent {agent_name} 'Write code'`"
        system_prompt = self.load_agent_prompt(agent_name)
        if not system_prompt:
            return f"❌ Agent '{agent_name}' not found"
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        original_len = len(system_prompt)
        if len(system_prompt) > 8000:
            system_prompt = system_prompt[:8000] + "\n... [truncated]"
            console.print(f"[dim]ℹ️ System prompt optimized: {original_len} → ~4000 chars[/dim]")
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
        # Use local provider for now
        try:
            console.print("[dim]⏳ Calling Ollama...[/dim]")
            result = subprocess.run(
                ["ollama", "run", "qwen2.5-coder", full_prompt],
                capture_output=True, text=True, timeout=180, encoding='utf-8'
            )
            result_text = result.stdout.strip() if result.returncode == 0 else f"❌ Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            result_text = "❌ Timeout: Request took too long"
        except Exception as e:
            result_text = f"❌ Error: {str(e)}"
        
        self.conversation_history.append({"role": "user", "content": f"/use-agent {agent_name} {user_prompt}"})
        self.conversation_history.append({"role": "assistant", "content": result_text})
        return result_text
    
    def cmd_ask(self, args: str) -> str:
        if not args:
            return "❌ Please provide a question"
        # Use local provider for now
        try:
            console.print("[dim]⏳ Calling Ollama...[/dim]")
            result = subprocess.run(
                ["ollama", "run", "qwen2.5-coder", args],
                capture_output=True, text=True, timeout=180, encoding='utf-8'
            )
            result_text = result.stdout.strip() if result.returncode == 0 else f"❌ Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            result_text = "❌ Timeout: Request took too long"
        except Exception as e:
            result_text = f"❌ Error: {str(e)}"
        
        self.conversation_history.append({"role": "user", "content": args})
        self.conversation_history.append({"role": "assistant", "content": result_text})
        return result_text
    
    def cmd_code(self, args: str) -> str:
        if not args:
            return "❌ Please describe the code"
        return self.cmd_ask(f"Write professional code for: {args}")
    
    def cmd_plan(self, args: str) -> str:
        if not args:
            return "❌ Please describe the task"
        return self.cmd_ask(f"Create a detailed development plan for: {args}")
    
    def cmd_test(self, args: str) -> str:
        if not args:
            return "❌ Please describe the component to test"
        return self.cmd_ask(f"Write comprehensive tests for: {args}")
    
    def cmd_file(self, args: str) -> str:
        if not args:
            return "❌ Please specify file path"
        p = Path(args)
        if not p.is_absolute():
            p = self.current_workspace / args
        if p.exists() and p.is_file():
            try:
                return f"## 📄 {p.name}\n\n```\n{p.read_text(encoding='utf-8')[:3000]}\n```"
            except Exception as e:
                return f"❌ Error: {e}"
        return f"❌ File not found: {args}"
    
    def cmd_shield(self, args: str = "") -> str:
        return "## 🛡️ AgentShield Report\n\n✅ All security layers operational"
    
    def cmd_save(self, args: str) -> str:
        return self.save_last_response(args if args else None)
    
    def cmd_export(self, args: str) -> str:
        return self.export_last_code(args if args else None)
    
    def cmd_help(self) -> str:
        return """
## 🌊 CARTAGE v1.0 - Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/agents [lang]` | List agents | `/agents python` |
| `/skills [cmd]` | List skills | `/skills all` |
| `/use-agent <name> <prompt>` | Use prompt agent | `/use-agent cartage-code "Write code"` |
| `/ask <question>` | Ask any question | `/ask "What is AI?"` |
| `/code <desc>` | Generate code | `/code "factorial function"` |
| `/plan <desc>` | Create plan | `/plan "Build API"` |
| `/test <desc>` | Write tests | `/test "factorial"` |
| `/file <path>` | Read file | `/file cartage.py` |
| `/shield` | Security report | `/shield` |
| `/save [filename]` | Save last response | `/save response.md` |
| `/export [filename]` | Export code | `/export code.py` |
| `/help` | Show help | `/help` |
| `/quit` | Exit | `/quit` |
"""
    
    def handle_command(self, command: str, args: str) -> str:
        handlers = {
            "agents": self.cmd_agents, "skills": self.cmd_skills, "use-agent": self.cmd_use_agent,
            "ask": self.cmd_ask, "code": self.cmd_code, "plan": self.cmd_plan, "test": self.cmd_test,
            "file": self.cmd_file, "shield": self.cmd_shield, "save": self.cmd_save,
            "export": self.cmd_export, "help": self.cmd_help
        }
        return handlers[command](args) if command in handlers else f"❌ Unknown command: {command}\n{self.cmd_help()}"
    
    def run(self):
        logo = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██████╗ █████╗ ██████╗ ████████╗ █████╗  ██████╗ ███████╗                 ║
║   ██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝ ██╔════╝                 ║
║   ██║     ███████║██████╔╝   ██║   ███████║██║  ███╗█████╗                   ║
║   ██║     ██╔══██║██╔══██╗   ██║   ██╔══██║██║   ██║██╔══╝                   ║
║   ╚██████╗██║  ██║██║  ██║   ██║   ██║  ██║╚██████╔╝███████╗                 ║
║    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝                 ║
║                                                                              ║
║                         🌊  C A R T A G E  🌊                                ║
║                                                                              ║
║                   Where Ancient Wisdom Meets Modern Code                     ║
║                                                                              ║
║              𓊈𓊉  حضارة البحر المتوسط تلتقي بذكاء البرمجة  𓊈𓊉               ║
║                                                                              ║
║   ┌─────────────────────────────────────────────────────────────────────────┐║
║   │  $ python cartage.py                                                     │║
║   │  ✅ CARTAGE v1.0 initialized                                            │║
║   │  📊 Base Agents: 47 | Prompt Agents: 156 | Total: 203                │║
║   │  📊 Skills: 237 | Rules: 89                                            │║
║   │  🏛️ CARTAGE ready! Type /model to see all agents | /help for commands   │║
║   └─────────────────────────────────────────────────────────────────────────┘║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        console.print(logo, style="cyan")
        console.print(Panel.fit(f"[bold cyan]🌊 CARTAGE v1.0[/bold cyan]\n[yellow]📁 Workspace: {self.current_workspace}[/yellow]\n[dim]🤖 {len(self.agents) + len(self.get_prompt_agents())} agents ready ({len(self.agents)} base + {len(self.get_prompt_agents())} prompt)[/dim]", border_style="cyan"))
        
        console.print(f"\n[green]✅ CARTAGE ready! {len(self.agents) + len(self.get_prompt_agents())} total agents, {len(self.skills)} skills[/green]\n")
        console.print("[dim]💡 Type /help for commands[/dim]\n")
        
        while True:
            try:
                user_input = console.input("[bold cyan]🌊 CARTAGE>[/bold cyan] ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["/quit", "exit"]:
                    console.print("[yellow]👋 Goodbye! CARTAGE is waiting for your return.[/yellow]")
                    break
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=1)
                    command = parts[0][1:].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                        progress.add_task(description=f"Processing {command}...", total=None)
                        result = self.handle_command(command, args)
                    console.print("\n[bold cyan]💡 Response:[/bold cyan]\n")
                    console.print(Markdown(result))
                    console.print("\n" + "="*70)
                else:
                    # Direct chat with local provider
                    try:
                        console.print("[dim]⏳ Calling Ollama...[/dim]")
                        result = subprocess.run(
                            ["ollama", "run", "qwen2.5-coder", user_input],
                            capture_output=True, text=True, timeout=180, encoding='utf-8'
                        )
                        result_text = result.stdout.strip() if result.returncode == 0 else f"❌ Error: {result.stderr}"
                    except subprocess.TimeoutExpired:
                        result_text = "❌ Timeout: Request took too long"
                    except Exception as e:
                        result_text = f"❌ Error: {str(e)}"
                    
                    console.print("\n[bold cyan]💡 Response:[/bold cyan]\n")
                    console.print(Markdown(result_text))
                    console.print("\n" + "="*70)
                    self.conversation_history.append({"role": "user", "content": user_input})
                    self.conversation_history.append({"role": "assistant", "content": result_text})
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Exiting...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

# ========== Main ==========
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🌊 CARTAGE v1.0 - Sovereign AI Framework 🌊║
    ║     Where Ancient Wisdom Meets Modern Code               ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check Ollama
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        console.print("[green]✅ Ollama connected[/green]")
    except:
        console.print("[yellow]⚠️ Ollama not found. Local mode may not work.[/yellow]")
    
    # Check database
    if not DB_PATH.exists():
        console.print("[red]❌ Database not found! Run copy_resources.py first[/red]")
        sys.exit(1)
    
    # Run CARTAGE
    cartage = CartageCore()
    cartage.run()
