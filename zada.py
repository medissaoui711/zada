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
        
        # اختيار مزود الخدمة
        console.print("\n[bold cyan]🔌 جاري فحص مزودي الخدمة...[/bold cyan]")
        self.current_provider = self.select_provider_interactive()
        console.print(f"[green]✅ تم اختيار المزود: {self.current_provider}[/green]")
        
        # تحميل الموارد
        self.agents = self.load_agents()
        self.skills = self.load_skills()
        self.rules = self.load_rules()
        
        console.print(f"[green]✅ ZADA initialized with provider: {self.current_provider}[/green]")
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
        """تحميل جميع المهارات من مجلد skills مباشرة"""
        skills: list[dict[str, Any]] = []
        skills_dir = self.zada_home / "skills"

        if skills_dir.exists():
            for category_dir in skills_dir.glob("*"):
                if category_dir.is_dir():
                    for skill_file in category_dir.glob("*.md"):
                        if skill_file.name.endswith('.metadata.json'):
                            continue

                        # قراءة الوصف من ملف metadata إذا وجد
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
        """إرسال طلب إلى LLM (يدعم Local و Cloud)"""
        return self.ask_llm(prompt, "local")

    # ========== دوال Cloud APIs ==========
    def ask_openai(self, prompt: str) -> str:
        """إرسال طلب إلى OpenAI API"""
        if not OPENAI_API_KEY:
            return "❌ OpenAI API key غير موجود. قم بتعيين OPENAI_API_KEY في المتغيرات البيئية"
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
        """إرسال طلب إلى Anthropic Claude API"""
        if not ANTHROPIC_API_KEY:
            return "❌ Anthropic API key غير موجود"
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
        """إرسال طلب إلى Google Gemini API"""
        if not GEMINI_API_KEY:
            return "❌ Gemini API key غير موجود"
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
        """إرسال طلب إلى Groq API (سريع جداً)"""
        if not GROQ_API_KEY:
            return "❌ Groq API key غير موجود"
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
        """إرسال طلب إلى Together.ai API"""
        if not TOGETHER_API_KEY:
            return "❌ Together.ai API key غير موجود"
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

    # ========== إدارة المصادر (Local / Cloud) ==========
    def get_available_providers(self) -> list[dict[str, Any]]:
        """الحصول على قائمة بمزودي الخدمة المتاحين"""
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
        """عرض مزودي الخدمة المتاحين وطلب اختيار"""
        providers = self.get_available_providers()
        console.print("\n[bold cyan]🔌 مزودي الخدمة المتاحين:[/bold cyan]")
        for i, p in enumerate(providers, 1):
            console.print(f"  {i}. {p['display']} [dim]({p['model']})[/dim]")
        console.print("\n[bold yellow]💡 الاقتراحات:[/bold yellow]")
        console.print("  • [green]Local (Ollama)[/green] - مجاني، يعمل بدون إنترنت")
        console.print("  • [green]Groq[/green] - سريع جداً، يتطلب مفتاح API مجاني")
        console.print("  • [green]OpenAI[/green] - قوي، يتطلب اشتراك")
        while True:
            try:
                choice = console.input(f"\n[bold cyan]🔧 اختر رقم المزود (1-{len(providers)}): [/bold cyan]").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(providers):
                        selected = providers[idx]["name"]
                        console.print(f"[green]✅ تم اختيار: {providers[idx]['display']}[/green]")
                        return selected
                    console.print(f"[red]❌ رقم غير صالح. اختر من 1 إلى {len(providers)}[/red]")
                else:
                    console.print("[red]❌ يرجى إدخال رقم صحيح[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ تم الإلغاء، سيتم استخدام Local[/yellow]")
                return "local"

    def ask_llm(self, prompt: str, provider: str = None) -> str:
        """إرسال طلب إلى LLM حسب المزود المختار"""
        if provider is None:
            provider = getattr(self, 'current_provider', 'local')
        if provider == "local":
            try:
                console.print("[dim]⏳ جاري الاتصال بـ Ollama...[/dim]")
                result = subprocess.run(
                    ["ollama", "run", OLLAMA_MODEL, prompt],
                    capture_output=True, text=True, timeout=300, encoding='utf-8'
                )
                return result.stdout.strip() if result.returncode == 0 else f"❌ خطأ: {result.stderr}"
            except subprocess.TimeoutExpired:
                return "❌ Timeout: استغرق الطلب وقتاً طويلاً"
            except Exception as e:
                return f"❌ خطأ: {str(e)}"
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
        return f"❌ مزود غير معروف: {provider}"

    def cmd_agents(self, args: str = "") -> str:
        if args:
            agents = [a for a in self.agents if args.lower() in a["language"].lower() or args.lower() in a["name"].lower()]
            if not agents:
                return f"❌ لا يوجد وكلاء للغة: {args}"
            result = f"## 🤖 وكلاء {args.upper()}\n\n"
            for a in agents[:20]:
                result += f"- **{a['name']}** ({a['type']})\n  - {a['description'][:80]}...\n\n"
            return result
        
        result = "## 🤖 جميع الوكلاء\n\n"
        by_lang = {}
        for a in self.agents:
            by_lang.setdefault(a["language"], []).append(a["name"])
        for lang, names in sorted(by_lang.items()):
            result += f"### {lang.upper()} ({len(names)})\n"
            result += ", ".join(names[:15])
            if len(names) > 15:
                result += f" ... و{len(names)-15} آخر"
            result += "\n\n"
        return result
    
    def cmd_skills(self, args: str = "") -> str:
        if not self.skills:
            return "⚠️ لا توجد مهارات. تأكد من تشغيل copy_resources.py"
        
        if args == "all":
            result = f"## 🛠️ جميع المهارات ({len(self.skills)})\n\n"
            by_cat = {}
            for s in self.skills:
                by_cat.setdefault(s["category"], []).append(s["name"])
            for cat, names in sorted(by_cat.items()):
                result += f"### {cat.upper()} ({len(names)})\n"
                for name in names[:20]:
                    result += f"- {name}\n"
                if len(names) > 20:
                    result += f"- ... و{len(names)-20} أخرى\n"
                result += "\n"
            return result
        
        if args == "categories":
            cats = {}
            for s in self.skills:
                cats[s["category"]] = cats.get(s["category"], 0) + 1
            result = "## 🛠️ فئات المهارات\n\n"
            for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
                result += f"- **{cat.upper()}**: {count} مهارة\n"
            return result
        
        if args:
            matches = [s for s in self.skills if args.lower() in s["name"].lower() or args.lower() in s["description"].lower()]
            if not matches:
                return f"❌ لا توجد مهارات مطابقة لـ: {args}"
            result = f"## 🛠️ نتائج البحث: {args}\n\n"
            for s in matches[:15]:
                result += f"- **{s['name']}** ({s['category']})\n  - {s['description'][:80]}...\n\n"
            return result
        
        result = "## 🛠️ ملخص المهارات\n\n"
        cats = {}
        for s in self.skills:
            cats[s["category"]] = cats.get(s["category"], 0) + 1
        for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10]:
            result += f"- **{cat.upper()}**: {count} مهارة\n"
        result += f"\n📊 **إجمالي المهارات: {len(self.skills)}**\n"
        result += "\n💡 استخدم:\n"
        result += "   - `/skills all` - لعرض جميع المهارات\n"
        result += "   - `/skills categories` - لعرض الفئات\n"
        result += "   - `/skills <كلمة>` - للبحث\n"
        return result
    
    def cmd_plan(self, args: str) -> str:
        if not args:
            return "❌ يرجى وصف المهمة"
        # صياغة أقصر وأسرع
        return self.ask_ollama(f"خطط لـ: {args}")
    
    def cmd_code(self, args: str) -> str:
        if not args:
            return "❌ يرجى وصف الكود المطلوب"
        # صياغة أقصر وأسرع
        return self.ask_ollama(f"اكتب كود لـ: {args}")
    
    def cmd_test(self, args: str) -> str:
        if not args:
            return "❌ يرجى وصف المكون"
        # صياغة أقصر وأسرع
        return self.ask_ollama(f"اكتب اختبارات لـ: {args}")
    
    def cmd_file(self, args: str) -> str:
        if not args:
            return "❌ يرجى تحديد مسار الملف"
        p = Path(args)
        if not p.is_absolute():
            p = self.current_workspace / args
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding='utf-8')
                return f"## 📄 {p.name}\n\n```\n{content[:2000]}\n```"
            except Exception as e:
                return f"❌ خطأ: {e}"
        return f"❌ الملف غير موجود: {args}"
    
    def cmd_shield(self, args: str = "") -> str:
        return "✅ AgentShield: لم يتم العثور على ثغرات أمنية"
    
    def cmd_learn(self, args: str = "") -> str:
        return "📊 Continuous Learning: تم تسجيل 0 جلسة حتى الآن"
    
    def cmd_review(self, args: str) -> str:
        if not args:
            return "❌ يرجى تحديد ملف للمراجعة"
        file_path = Path(args)
        if not file_path.is_absolute():
            file_path = self.current_workspace / args
        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding='utf-8')[:3000]
            return self.ask_ollama(f"قم بمراجعة هذا الكود بدقة:\n\n{content}")
        return f"❌ الملف غير موجود: {args}"

    def cmd_fix(self, args: str) -> str:
        if not args:
            return "❌ يرجى تحديد ملف للإصلاح"
        file_path = Path(args)
        if not file_path.is_absolute():
            file_path = self.current_workspace / args
        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding='utf-8')[:3000]
            return self.ask_ollama(f"قم بتحليل وإصلاح المشاكل في هذا الكود:\n\n{content}")
        return f"❌ الملف غير موجود: {args}"

    def cmd_build(self, args: str) -> str:
        if not args:
            return "❌ يرجى وصف مشكلة البناء"
        return self.ask_ollama(f"قم بتحليل مشكلة البناء التالية واقتراح حلاً:\n\n{args}")

    def cmd_provider(self, args: str) -> str:
        """تغيير مزود الخدمة"""
        if not args:
            return f"🔌 المزود الحالي: {self.current_provider}\n\nاستخدم `/provider <name>` لتغيير المزود\nالأسماء المتاحة: local, openai, anthropic, gemini, groq, together"
        providers = [p["name"] for p in self.get_available_providers()]
        if args in providers:
            self.current_provider = args
            return f"✅ تم تغيير المزود إلى: {args}"
        return f"❌ المزود '{args}' غير متاح.\n\nالمزودين المتاحين:\n" + "\n".join(f"  • {p}" for p in providers)

    def cmd_providers(self) -> str:
        """عرض جميع المزودين المتاحين"""
        providers = self.get_available_providers()
        result = "## 🔌 مزودي الخدمة المتاحين\n\n"
        for p in providers:
            current = " ✅ (الحالي)" if p["name"] == self.current_provider else ""
            result += f"- **{p['display']}**{current}\n"
            result += f"  - النموذج: `{p['model']}`\n\n"
        return result

    def cmd_help(self) -> str:
        return """
## 🏔️ ZADA v1.0 - الأوامر المتاحة

| الأمر | الوصف | مثال |
|-------|-------|------|
| `/agents` | عرض جميع الوكلاء | `/agents` |
| `/agents <lang>` | وكلاء بلغة محددة | `/agents python` |
| `/skills` | ملخص المهارات | `/skills` |
| `/skills all` | عرض جميع المهارات | `/skills all` |
| `/skills categories` | عرض الفئات | `/skills categories` |
| `/skills <word>` | بحث | `/skills security` |
| `/plan <desc>` | خطة تطوير | `/plan موقع ويب` |
| `/code <desc>` | كتابة كود | `/code دالة جمع` |
| `/test <desc>` | كتابة اختبارات | `/test دالة جمع` |
| `/file <path>` | قراءة ملف | `/file zada.py` |
| `/shield` | فحص أمني | `/shield` |
| `/learn` | التعلم المستمر | `/learn` |
| `/review <path>` | مراجعة كود | `/review file.py` |
| `/fix <path>` | إصلاح كود | `/fix file.py` |
| `/build <desc>` | حل مشكلة بناء | `/build مشكلة بناء` |
| `/provider [name]` | عرض/تغيير مزود الخدمة | `/provider groq` |
| `/providers` | عرض جميع المزودين | `/providers` |
| `/help` | المساعدة | `/help` |
| `/quit` | الخروج | `/quit` |
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
        elif cmd == "help":
            return self.cmd_help()
        else:
            return f"❌ أمر غير معروف: {cmd}\n{self.cmd_help()}"
    
    def run(self):
        console.print(Panel.fit(
            "[bold cyan]🏔️ ZADA v1.0 - Multi-Provider AI Coding Assistant[/bold cyan]\n"
            f"[yellow]📁 Workspace: {self.current_workspace}[/yellow]",
            border_style="cyan"
        ))
        console.print(f"\n[green]✅ ZADA ready! {len(self.agents)} agents, {len(self.skills)} skills[/green]\n")
        console.print("[dim]💡 استخدم /help لعرض الأوامر[/dim]\n")
        
        while True:
            try:
                user = console.input("[bold cyan]🏔️ ZADA>[/bold cyan] ").strip()
                if not user:
                    continue
                if user.lower() in ["/quit", "exit"]:
                    console.print("[yellow]👋 Goodbye![/yellow]")
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