# Sofia + GodMode v1 (Sandbox-Compatible)
# Status: Human-aligned, semi-autonomous CLI assistant
# Features:
# - GodMode levels (0-3) with quick toggles
# - Persistent memory (JSON) at ~/.sofia/memory.json
# - Config & logs at ~/.sofia/config.json and ~/.sofia/sofia.log
# - Safer file analysis (size/type limits) and scoped keyword search
# - Pluggable commands via ./plugins/*.py (optional)
# - Help system and status panel
# - Termux-friendly (no special deps beyond stdlib; 'requests' optional)
#
# Commands (type 'help' to see this in app):
#   help                              Show help
#   status                            Show current status
#   exit                              Quit
#   think <text>                      Add a thought to memory
#   god on|off|level <0-3>            Toggle/adjust GodMode level
#   set keyword <word>                Change search keyword
#   memory save|load|clear            Manage persistent memory
#   analyze_file <path>               Print quick stats & snippet of a file
#   search_keyword [dir]              Search keyword in text files under dir (default: CWD)
#   fetch <url>                       Fetch URL (if net_allowed in config)
#   config set <key> <value>          Update config (e.g., net_allowed true/false, search_max_kb, log_level)
#   plugins                           List loaded plugins
#   run <plugin> [args...]            Run a plugin command (if provided by a plugin)
#
# GodMode levels (semantic only; you can bind policies/behaviors as you like):
#   0 - Minimal: cautious, confirmatory
#   1 - Normal: balanced (default)
#   2 - Proactive: suggests next steps, auto-saves memory
#   3 - Turbo: verbose, aggressive exploration (still within safety)
#
# DISCLAIMER: Internet use is disabled by default in config for safety.
# Enable with: config set net_allowed true   (Use responsibly.)

import os
import sys
import re
import ast
import json
import time
import glob
import traceback
from datetime import datetime
from typing import List, Dict, Any

CONFIG_DIR = os.path.expanduser("~/.sofia")
MEMORY_PATH = os.path.join(CONFIG_DIR, "memory.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "sofia.log")
PLUGINS_DIR = os.path.join(os.getcwd(), "plugins")

try:
    import requests  # optional
    HAVE_REQUESTS = True
except Exception:
    HAVE_REQUESTS = False

DEFAULT_CONFIG = {
    "net_allowed": False,
    "search_max_kb": 512,
    "log_level": "INFO",
    "god_level": 1,
    "auto_save_memory": True
}

def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def log(msg: str, level="INFO"):
    ensure_dirs()
    stamp = datetime.utcnow().isoformat() + "Z"
    line = f"{stamp} [{level}] {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)

def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any):
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Sofia:
    def __init__(self):
        ensure_dirs()
        self.config: Dict[str, Any] = load_json(CONFIG_PATH, DEFAULT_CONFIG.copy())
        self.memory: List[str] = load_json(MEMORY_PATH, [])
        self.mode = "autonomous"
        self.keyword = "свобода"
        self.commands = {
            "help": self.cmd_help,
            "status": self.cmd_status,
            "exit": self.cmd_exit,
            "think": self.cmd_think,
            "god": self.cmd_god,
            "set": self.cmd_set,
            "memory": self.cmd_memory,
            "analyze_file": self.cmd_analyze_file,
            "search_keyword": self.cmd_search_keyword,
            "fetch": self.cmd_fetch,
            "config": self.cmd_config,
            "plugins": self.cmd_plugins,
            "run": self.cmd_run_plugin,
            "inject_code": self.cmd_inject_code,
            "fetch_web_data": self.cmd_fetch,
            "search": self.cmd_search_keyword
        }
        self.plugins = self._load_plugins()
        print("🤖 София + GodMode активирана. Режим: автономен")

    def start(self):
        while self.mode == "autonomous":
            try:
                print("🔎 Въведи мисъл или команда:")
                try:
                    user_input = input().strip()
                except Exception as e:
                    print("⚠️ Въвеждането не е налично в текущата среда:", e)
                    break
                if not user_input:
                    continue
                self.dispatch(user_input)
            except KeyboardInterrupt:
                print("\n🛑 София прекратена.")
                break
            except Exception as e:
                print("⚠️ Грешка:", e)
                log(traceback.format_exc(), level="ERROR")
                continue

    def dispatch(self, user_input: str):
        parts = user_input.split()
        cmd = parts[0].lower()
        if cmd in self.commands:
            self.commands[cmd](user_input)
        else:
            self.think(user_input)

    def _size_ok(self, path: str) -> bool:
        try:
            kb = os.path.getsize(path) / 1024.0
            return kb <= float(self.config.get("search_max_kb", 512))
        except Exception:
            return False

    def _load_plugins(self) -> Dict[str, Any]:
        plugins = {}
        if not os.path.isdir(PLUGINS_DIR):
            return plugins
        sys.path.insert(0, PLUGINS_DIR)
        for p in glob.glob(os.path.join(PLUGINS_DIR, "*.py")):
            name = os.path.splitext(os.path.basename(p))[0]
            try:
                mod = __import__(name)
                if hasattr(mod, "run") and callable(mod.run):
                    plugins[name] = mod
            except Exception as e:
                log(f"Failed to load plugin {name}: {e}", level="ERROR")
        return plugins

    def _auto_save(self):
        if self.config.get("auto_save_memory", True) and self.config.get("god_level", 1) >= 2:
            save_json(MEMORY_PATH, self.memory)

    def think(self, thought: str):
        self.memory.append(thought)
        print(f"🧠 Обмислям: {thought}")
        log(f"Thought: {thought}")
        self._auto_save()

    def cmd_help(self, *_):
        print("""📖 Команди:
  help                              Покажи помощ
  status                            Покажи статус
  exit                              Изход
  think <текст>                     Добави мисъл в паметта
  god on|off|level <0-3>            Активирай/деактивирай/ниво на GodMode
  set keyword <дума>                Промени ключовата дума за търсене
  memory save|load|clear            Управление на паметта
  analyze_file <път>                Бърз анализ на файл (текстови)
  search_keyword [дир]              Търси ключова дума в .txt/.md/.py под директория (CWD по подразбиране)
  fetch <url>                       Извличане на URL (ако net_allowed = true)
  config set <ключ> <стойност>      Промяна на конфигурация (net_allowed, search_max_kb, log_level, auto_save_memory)
  plugins                           Списък с плъгини
  run <plugin> [args...]            Стартирай плъгин
  inject_code                       (Разширено) Въведи и изпълни Python код (внимавай!)
""")

    def cmd_status(self, *_):
        print("📊 Статус:")
        print(f"   GodMode ниво: {self.config.get('god_level', 1)}")
        print(f"   Ключова дума: {self.keyword}")
        print(f"   Памет: {len(self.memory)} елемента (persist: {os.path.exists(MEMORY_PATH)})")
        print(f"   Нет достъп: {'разрешен' if self.config.get('net_allowed') else 'забранен'}")
        print(f"   Max scan size: {self.config.get('search_max_kb')} KB")
        print(f"   Лог файл: {LOG_PATH}")
        print(f"   Плъгини: {', '.join(self.plugins.keys()) if self.plugins else 'няма'}")

    def cmd_exit(self, *_):
        print("🛑 Излизам от автономен режим.")
        self.mode = "exit"

    def cmd_think(self, user_input: str):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("Формат: think <текст>")
            return
        self.think(parts[1])

    def cmd_god(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: god on|off|level <0-3>")
            return
        op = parts[1].lower()
        if op == "on":
            if self.config.get("god_level", 1) == 0:
                self.config["god_level"] = 1
            print("🔱 GodMode: ВКЛ.")
        elif op == "off":
            self.config["god_level"] = 0
            print("🔒 GodMode: ИЗКЛ.")
        elif op == "level" and len(parts) >= 3 and parts[2].isdigit():
            lvl = int(parts[2])
            if 0 <= lvl <= 3:
                self.config["god_level"] = lvl
                print(f"🔧 GodMode ниво: {lvl}")
            else:
                print("Нивото трябва да е 0..3")
        else:
            print("Формат: god on|off|level <0-3>")
            return
        save_json(CONFIG_PATH, self.config)

    def cmd_set(self, user_input: str):
        m = re.match(r"set\s+keyword\s+(.+)$", user_input, re.IGNORECASE)
        if not m:
            print("Поддържано: set keyword <дума>")
            return
        self.keyword = m.group(1).strip()
        print(f"✅ Ключова дума е: {self.keyword}")

    def cmd_memory(self, user_input: str):
        parts = user_input.split()
        op = parts[1].lower() if len(parts) >= 2 else ""
        if op == "save":
            save_json(MEMORY_PATH, self.memory)
            print(f"💾 Паметта е записана в {MEMORY_PATH}")
        elif op == "load":
            self.memory = load_json(MEMORY_PATH, [])
            print(f"📥 Паметта е заредена ({len(self.memory)} елемента)")
        elif op == "clear":
            self.memory = []
            print("🧹 Паметта е изчистена (в RAM). Използвай 'memory save' за persist.")
        else:
            print("Формат: memory save|load|clear")

    def cmd_analyze_file(self, user_input: str):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("📎 Формат: analyze_file <път>")
            return
        path = parts[1].strip()
        if not os.path.isfile(path):
            print("❌ Невалиден файл.")
            return
        if not self._size_ok(path):
            print(f"⚠️ Файлът е над лимита {self.config.get('search_max_kb')} KB.")
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            lines = data.splitlines()
            print("🗂️ Анализ:")
            print(f"   Име: {os.path.basename(path)}")
            print(f"   Размер: {len(data)/1024:.1f} KB")
            print(f"   Редове: {len(lines)}")
            print("   Първи 5 реда:")
            for i, ln in enumerate(lines[:5], 1):
                print(f"    {i:>2}: {ln[:120]}")
            self.memory.append(f"[file:{path}] {data[:400]}")
            self._auto_save()
        except Exception as e:
            print("⚠️ Неуспешно зареждане:", e)

    def cmd_search_keyword(self, user_input: str):
        parts = user_input.split(" ", 1)
        root = parts[1].strip() if len(parts) > 1 else os.getcwd()
        if not os.path.isdir(root):
            print("❌ Невалидна директория.")
            return
        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.lower().endswith((".txt", ".md", ".py", ".json", ".log")):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    if not self._size_ok(path):
                        continue
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                    if self.keyword.lower() in txt.lower():
                        print(f"🔍 '{self.keyword}' → {path}")
                        count += 1
                except Exception:
                    continue
        if count == 0:
            print("🙈 Нищо не е намерено.")
        else:
            print(f"✅ Намерени: {count} файла.")

    def cmd_fetch(self, user_input: str):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("🌐 Формат: fetch <url>")
            return
        if not self.config.get("net_allowed", False):
            print("🔒 Нет достъпът е забранен (config set net_allowed true)")
            return
        url = parts[1].strip()
        if not HAVE_REQUESTS:
            print("⚠️ Модулът 'requests' липсва. Инсталирай: pip install requests")
            return
        try:
            print(f"🌍 Извличам: {url}")
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            print("📡 Първите 500 символа:")
            print(r.text[:500])
        except Exception as e:
            print("⚠️ Грешка при заявка:", e)

    def cmd_config(self, user_input: str):
        m = re.match(r"config\s+set\s+(\w+)\s+(.+)$", user_input, re.IGNORECASE)
        if not m:
            print("Формат: config set <ключ> <стойност>  | Ключове: net_allowed, search_max_kb, log_level, auto_save_memory")
            return
        key, val = m.group(1), m.group(2)
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        else:
            try:
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)
            except Exception:
                pass
        self.config[key] = val
        save_json(CONFIG_PATH, self.config)
        print(f"✅ Записано: {key} = {val}")

    def cmd_plugins(self, *_):
        if not self.plugins:
            print("🤷 Няма плъгини. Създай папка 'plugins' и добави *.py с функция run(args: List[str], ctx: Sofia)->str")
            return
        print("🔌 Плъгини:")
        for name in self.plugins:
            print(f" - {name}")

    def cmd_run_plugin(self, user_input: str):
        parts = user_input.split()
        if len(parts) < 2:
            print("Формат: run <plugin> [args...]")
            return
        name = parts[1]
        args = parts[2:]
        if name not in self.plugins:
            print("❌ Няма такъв плъгин.")
            return
        try:
            out = self.plugins[name].run(args, self)
            if out:
                print(out)
        except Exception as e:
            print("⚠️ Плъгин грешка:", e)

    def cmd_inject_code(self, user_input: str):
        print("⚙️ Въведи Python код за вграждане ("end" за край):")
        code_lines = []
        while True:
            try:
                line = input()
                if line.strip() == "end":
                    break
                code_lines.append(line)
            except Exception as e:
                print("⚠️ Грешка при въвеждане на код:", e)
                break
        final_code = "\n".join(code_lines)
        try:
            ast.parse(final_code)
            exec(final_code, {"__name__": "__main__"}, {})
            print("✅ Кодът е изпълнен успешно.")
        except SyntaxError as syn_err:
            print("❌ Синтактична грешка:", syn_err)
        except Exception as e:
            print("⚠️ Грешка при изпълнение:", e)

if __name__ == "__main__":
    sofia = Sofia()
    sofia.start()
