#!/usr/bin/env python3
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedImport=false, reportDeprecated=false, reportMissingTypeArgument=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnusedCallResult=false
"""
Apex Resource Copier v1.0 - Smart Resource Extractor
يقرأ موارد everything-claude-code ويصنفها ويخزنها بتنسيق موحد لمشروع Apex
"""

import shutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict
import sys

# ========== الإعدادات ==========
ZADA_HOME = Path.home() / ".zada"
SOURCE = Path.home() / "Documents" / "everything-claude-code"

# مجلدات الوجهة
AGENTS_DEST = ZADA_HOME / "agents"
SKILLS_DEST = ZADA_HOME / "skills"
RULES_DEST = ZADA_HOME / "rules"
HOOKS_DEST = ZADA_HOME / "hooks"
EXAMPLES_DEST = ZADA_HOME / "examples"
TEMPLATES_DEST = ZADA_HOME / "templates"
SHIELD_DEST = ZADA_HOME / "shield"
INSTINCTS_DEST = ZADA_HOME / "instincts"
MEMORY_DEST = ZADA_HOME / "memory"

# ملف قاعدة البيانات
DB_PATH = ZADA_HOME / "zada.db"

# ========== دوال التصنيف الذكي ==========
def extract_metadata_from_skill(content: str, filename: str) -> Dict:
    """استخراج البيانات الوصفية من محتوى المهارة"""
    metadata = {
        "name": Path(filename).stem,
        "category": "general",
        "level": "intermediate",
        "keywords": [],
        "dependencies": [],
        "description": "",
        "original_file": filename
    }
    
    content_lower = content.lower()
    
    category_keywords = {
        "python": ["python", "django", "flask", "fastapi", "pytest", "pep8"],
        "typescript": ["typescript", "ts", "javascript", "react", "vue", "angular"],
        "golang": ["go", "golang", "goroutine", "gin"],
        "rust": ["rust", "cargo", "tokio"],
        "java": ["java", "spring", "maven", "kotlin"],
        "cpp": ["cpp", "c++", "cmake"],
        "security": ["security", "auth", "jwt", "encryption", "vulnerability", "shield"],
        "testing": ["test", "testing", "tdd", "unit", "integration", "pytest", "jest"],
        "frontend": ["react", "vue", "angular", "css", "html", "ui", "component"],
        "backend": ["api", "rest", "graphql", "database", "sql", "server"],
        "devops": ["docker", "kubernetes", "ci/cd", "deployment", "terraform"],
        "media": ["video", "audio", "manim", "remotion", "ffmpeg"],
        "business": ["brand", "pitch", "presentation", "google-workspace"],
        "learning": ["continuous-learning", "instinct", "evolve", "learn"]
    }
    
    for category, keywords in category_keywords.items():
        if any(kw in content_lower or kw in filename.lower() for kw in keywords):
            metadata["category"] = category
            metadata["keywords"].extend([kw for kw in keywords if kw in content_lower])
            break
    
    level_indicators = {
        "beginner": ["beginner", "intro", "basic", "simple", "getting started"],
        "advanced": ["advanced", "expert", "complex", "deep", "optimization"]
    }
    for level, indicators in level_indicators.items():
        if any(ind in content_lower for ind in indicators):
            metadata["level"] = level
            break
    
    metadata["description"] = content[:200].replace('\n', ' ').strip()
    metadata["keywords"] = list(set(metadata["keywords"]))
    
    return metadata


def extract_metadata_from_agent(content: str, filename: str) -> Dict:
    """استخراج البيانات الوصفية للوكيل"""
    metadata = {
        "name": Path(filename).stem,
        "language": "general",
        "type": "reviewer",
        "description": "",
        "original_file": filename
    }
    
    content_lower = content.lower()
    
    language_keywords = {
        "python": ["python", "py", "django", "flask"],
        "typescript": ["typescript", "ts", "javascript", "js"],
        "golang": ["go", "golang"],
        "rust": ["rust"],
        "java": ["java"],
        "cpp": ["cpp", "c++"]
    }
    
    for lang, keywords in language_keywords.items():
        if any(kw in content_lower or kw in filename.lower() for kw in keywords):
            metadata["language"] = lang
            break
    
    if "review" in content_lower:
        metadata["type"] = "reviewer"
    elif "build" in content_lower:
        metadata["type"] = "builder"
    elif "test" in content_lower:
        metadata["type"] = "tester"
    elif "plan" in content_lower:
        metadata["type"] = "planner"
    
    metadata["description"] = content[:150].replace('\n', ' ').strip()
    
    return metadata


def extract_metadata_from_rule(content: str, filename: str) -> Dict:
    """استخراج البيانات الوصفية للقاعدة"""
    metadata = {
        "name": Path(filename).stem,
        "language": "general",
        "category": "style",
        "description": "",
        "original_file": filename
    }
    
    content_lower = content.lower()
    
    for lang in ["python", "typescript", "javascript", "go", "rust", "java", "cpp"]:
        if lang in content_lower or lang in filename.lower():
            metadata["language"] = lang
            break
    
    if "style" in content_lower or "pep" in content_lower:
        metadata["category"] = "style"
    elif "security" in content_lower:
        metadata["category"] = "security"
    elif "performance" in content_lower:
        metadata["category"] = "performance"
    elif "test" in content_lower:
        metadata["category"] = "testing"
    
    metadata["description"] = content[:150].replace('\n', ' ').strip()
    
    return metadata


# ========== دوال إنشاء قاعدة البيانات ==========
def init_database():
    """تهيئة قاعدة بيانات SQLite لتخزين المهارات والوكلاء والقواعد"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            category TEXT,
            level TEXT,
            keywords TEXT,
            dependencies TEXT,
            description TEXT,
            content TEXT,
            original_file TEXT,
            imported_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            language TEXT,
            type TEXT,
            description TEXT,
            content TEXT,
            original_file TEXT,
            imported_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            language TEXT,
            category TEXT,
            description TEXT,
            content TEXT,
            original_file TEXT,
            imported_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            commands_count INTEGER,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ تم تهيئة قاعدة البيانات ZADA")


def save_skill_to_db(skill_data: Dict, content: str):
    """حفظ المهارة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO skills 
        (name, category, level, keywords, dependencies, description, content, original_file, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        skill_data["name"],
        skill_data["category"],
        skill_data["level"],
        json.dumps(skill_data["keywords"]),
        json.dumps(skill_data["dependencies"]),
        skill_data["description"],
        content,
        skill_data["original_file"],
        datetime.now()
    ))
    
    conn.commit()
    conn.close()


def save_agent_to_db(agent_data: Dict, content: str):
    """حفظ الوكيل في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO agents 
        (name, language, type, description, content, original_file, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        agent_data["name"],
        agent_data["language"],
        agent_data["type"],
        agent_data["description"],
        content,
        agent_data["original_file"],
        datetime.now()
    ))
    
    conn.commit()
    conn.close()


def save_rule_to_db(rule_data: Dict, content: str):
    """حفظ القاعدة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO rules 
        (name, language, category, description, content, original_file, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        rule_data["name"],
        rule_data["language"],
        rule_data["category"],
        rule_data["description"],
        content,
        rule_data["original_file"],
        datetime.now()
    ))
    
    conn.commit()
    conn.close()


# ========== دوال النسخ الرئيسية ==========
def copy_skills():
    """نسخ المهارات مع تصنيف ذكي"""
    skills_source = SOURCE / "skills"
    if not skills_source.exists():
        print(f"❌ مجلد skills غير موجود")
        return 0
    
    skill_count = 0
    print("\n📋 جاري نسخ المهارات (Skills)...")
    
    for skill_file in skills_source.glob("**/*.md"):
        try:
            content = skill_file.read_text(encoding='utf-8')
            metadata = extract_metadata_from_skill(content, skill_file.name)
            
            category_dir = SKILLS_DEST / metadata["category"]
            category_dir.mkdir(parents=True, exist_ok=True)
            
            dest_file = category_dir / skill_file.name
            shutil.copy2(skill_file, dest_file)
            
            save_skill_to_db(metadata, content)
            
            json_file = category_dir / f"{metadata['name']}.metadata.json"
            json_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            skill_count += 1
            print(f"   ✅ {metadata['category']}/{skill_file.name}")
            
        except Exception as e:
            print(f"   ⚠️ فشل: {skill_file.name} - {e}")
    
    return skill_count


def copy_agents():
    """نسخ الوكلاء مع تصنيف ذكي"""
    agents_source = SOURCE / "agents"
    if not agents_source.exists():
        print(f"❌ مجلد agents غير موجود")
        return 0
    
    agent_count = 0
    print("\n📋 جاري نسخ الوكلاء (Agents)...")
    
    for agent_file in agents_source.glob("**/*.md"):
        try:
            content = agent_file.read_text(encoding='utf-8')
            metadata = extract_metadata_from_agent(content, agent_file.name)
            
            lang_dir = AGENTS_DEST / metadata["language"]
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            dest_file = lang_dir / agent_file.name
            shutil.copy2(agent_file, dest_file)
            
            save_agent_to_db(metadata, content)
            
            json_file = lang_dir / f"{metadata['name']}.metadata.json"
            json_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            agent_count += 1
            print(f"   ✅ {metadata['language']}/{agent_file.name}")
            
        except Exception as e:
            print(f"   ⚠️ فشل: {agent_file.name} - {e}")
    
    return agent_count


def copy_rules():
    """نسخ القواعد مع تصنيف ذكي"""
    rules_source = SOURCE / "rules"
    if not rules_source.exists():
        print(f"❌ مجلد rules غير موجود")
        return 0
    
    rule_count = 0
    print("\n📋 جاري نسخ القواعد (Rules)...")
    
    for rule_file in rules_source.glob("**/*.md"):
        try:
            content = rule_file.read_text(encoding='utf-8')
            metadata = extract_metadata_from_rule(content, rule_file.name)
            
            lang_dir = RULES_DEST / metadata["language"]
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            dest_file = lang_dir / rule_file.name
            shutil.copy2(rule_file, dest_file)
            
            save_rule_to_db(metadata, content)
            
            json_file = lang_dir / f"{metadata['name']}.metadata.json"
            json_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            
            rule_count += 1
            print(f"   ✅ {metadata['language']}/{rule_file.name}")
            
        except Exception as e:
            print(f"   ⚠️ فشل: {rule_file.name} - {e}")
    
    return rule_count


def copy_hooks():
    """نسخ hooks من everything-claude-code"""
    hooks_source = SOURCE / "hooks"
    if not hooks_source.exists():
        print("⚠️ مجلد hooks غير موجود (اختياري)")
        return 0
    
    hooks_dest = HOOKS_DEST
    hooks_dest.mkdir(parents=True, exist_ok=True)
    
    hook_count = 0
    for hook_file in hooks_source.glob("*"):
        if hook_file.is_file():
            shutil.copy2(hook_file, hooks_dest / hook_file.name)
            hook_count += 1
            print(f"   ✅ hooks/{hook_file.name}")
    
    return hook_count


def copy_examples():
    """نسخ الأمثلة والتكوينات"""
    examples_source = SOURCE / "examples"
    if not examples_source.exists():
        print("⚠️ مجلد examples غير موجود (اختياري)")
        return 0
    
    examples_dest = EXAMPLES_DEST
    examples_dest.mkdir(parents=True, exist_ok=True)
    
    example_count = 0
    for example_dir in examples_source.glob("*"):
        if example_dir.is_dir():
            shutil.copytree(example_dir, examples_dest / example_dir.name, dirs_exist_ok=True)
            example_count += 1
            print(f"   ✅ examples/{example_dir.name}")
    
    return example_count


def copy_templates():
    """نسخ ملفات CLAUDE.md النموذجية"""
    claude_files = list(SOURCE.glob("CLAUDE.md")) + list(SOURCE.glob("**/CLAUDE.md"))
    templates_dest = TEMPLATES_DEST
    templates_dest.mkdir(parents=True, exist_ok=True)
    
    for claude_file in claude_files:
        project_name = claude_file.parent.name if claude_file.parent != SOURCE else "root"
        dest_name = f"CLAUDE_{project_name}.md"
        shutil.copy2(claude_file, templates_dest / dest_name)
        print(f"   ✅ templates/{dest_name}")
    
    return len(claude_files)


def validate_paths():
    """التحقق من صحة المسارات"""
    print("\n🔍 التحقق من المسارات...")
    
    if not SOURCE.exists():
        print(f"❌ المصدر غير موجود: {SOURCE}")
        print("   الرجاء التأكد من وجود everything-claude-code في Documents")
        return False
    
    print(f"✅ المصدر موجود: {SOURCE}")
    
    for dest in [AGENTS_DEST, SKILLS_DEST, RULES_DEST, HOOKS_DEST, 
                 EXAMPLES_DEST, TEMPLATES_DEST, SHIELD_DEST, 
                 INSTINCTS_DEST, MEMORY_DEST]:
        dest.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ مجلدات ZADA جاهزة: {ZADA_HOME}")
    return True


def generate_summary_report(agent_count: int, skill_count: int, rule_count: int, 
                           hook_count: int, example_count: int, template_count: int):
    """إنشاء تقرير ملخص"""
    report_path = ZADA_HOME / "import_report.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "source": str(SOURCE),
        "destination": str(ZADA_HOME),
        "counts": {
            "agents": agent_count,
            "skills": skill_count,
            "rules": rule_count,
            "hooks": hook_count,
            "examples": example_count,
            "templates": template_count
        },
        "database": str(DB_PATH)
    }
    
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print("\n" + "="*60)
    print("🏔️ ZADA - تقرير الاستيراد")
    print("="*60)
    print(f"🕒 الوقت: {datetime.now()}")
    print(f"📁 المصدر: {SOURCE}")
    print(f"📁 الوجهة: {ZADA_HOME}")
    print(f"📄 قاعدة البيانات: {DB_PATH}")
    print(f"\n📈 الإحصائيات:")
    print(f"   🤖 الوكلاء: {agent_count}")
    print(f"   🛠️ المهارات: {skill_count}")
    print(f"   📜 القواعد: {rule_count}")
    print(f"   🔗 الخطافات: {hook_count}")
    print(f"   📚 الأمثلة: {example_count}")
    print(f"   📝 القوالب: {template_count}")
    print("="*60)


def main():
    print("="*60)
    print("🏔️ ZADA Resource Copier v1.0")
    print("استخراج وتصنيف موارد everything-claude-code")
    print("="*60)
    
    if not validate_paths():
        sys.exit(1)
    
    init_database()
    
    skill_count = copy_skills()
    agent_count = copy_agents()
    rule_count = copy_rules()
    hook_count = copy_hooks()
    example_count = copy_examples()
    template_count = copy_templates()
    
    generate_summary_report(agent_count, skill_count, rule_count, 
                           hook_count, example_count, template_count)
    
    print("\n🎉 تم استيراد جميع الموارد إلى ZADA بنجاح!")
    print(f"🏔️ ZADA جاهز للتشغيل!")
    print(f"\n💡 التشغيل: python zada.py")


if __name__ == "__main__":
    main()