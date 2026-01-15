# -*- coding: utf-8 -*-
"""
PROJECT RELICT: ARTYOM INFINITE CORE [V6 - ENHANCED AAAA CORE]
Final Integrated Version
- Logging, persistence, plugin system
- Threaded LLM calls with dynamic psycho-spinner
- Bounded history (RAG-light)
- Runtime commands (!inspect, !reset, !mode, !modules, !reloadmodules, !save, !quit)
- Safe prompt builder integrating psycho engine state + memory
- Dynamic typing speed based on panic levels
- Strict executor name enforcement (beliytoporik)
"""

from __future__ import annotations
import os
import sys
import time
import json
import re
import requests
import threading
import importlib.util
import traceback
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List
import win32gui
from colorama import init, Fore, Style

# Инициализация colorama для Windows
init(autoreset=True)

# ---------------- Configuration ----------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "DATA"
ENT_FILE = BASE_DIR / "ENT.txt"
MODULES_DIR = BASE_DIR / "modules"
LOG_FILE = DATA_DIR / "artyom_core.log"
HISTORY_FILE = DATA_DIR / "messages.json"

# Создание структуры папок
DATA_DIR.mkdir(exist_ok=True)
MODULES_DIR.mkdir(exist_ok=True)

# LLM endpoint
DEFAULT_API_URL = "http://localhost:5001/api/v1/generate"
API_URL = os.getenv("LLM_API_URL", DEFAULT_API_URL)

# Настройки рантайма
MAX_HISTORY_ITEMS = 40        # Лимит истории для контекста
REQUEST_TIMEOUT = 25          # Таймаут запроса к LLM
RETRY_ATTEMPTS = 2
RETRY_BACKOFF = 1.2
THREAD_POOL_WORKERS = 2

# ---------------- Logging ----------------
logger = logging.getLogger("ArtyomCore")
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

# Вывод критических ошибок в консоль
console = logging.StreamHandler(sys.stdout)
console.setFormatter(fmt)
console.setLevel(logging.INFO)
logger.addHandler(console)

# ---------------- Load psycho engine dynamically ----------------
try:
    engine_file = next((f for f in os.listdir(BASE_DIR) if f.startswith("advanced_psycho")), None)
    if not engine_file:
        raise FileNotFoundError("Файл психо-движка (advanced_psycho*.py) не найден.")
    
    spec = importlib.util.spec_from_file_location("engine", str(BASE_DIR / engine_file))
    eng_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eng_mod)
    AdvancedPsychoEngine = eng_mod.AdvancedPsychoEngine
except Exception as e:
    logger.exception("Failed to load psycho engine: %s", e)
    print(Fore.RED + "КРИТИЧЕСКИЙ СБОЙ: Психо-движок не загружен. Проверь логи.")
    sys.exit(1)

# ---------------- Utilities ----------------
def safe_read_text(p: Path, default: str = "") -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return default

def clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, x))

# ---------------- Plugin system ----------------
class PluginManager:
    """Система загрузки внешних модулей из папки modules/"""
    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self.plugins = {}  # name -> module

    def discover(self) -> List[str]:
        return [p.name for p in self.modules_dir.glob("*.py")]

    def load_all(self, core):
        found = self.discover()
        for name in found:
            self.load(name, core)

    def load(self, filename: str, core):
        path = self.modules_dir / filename
        modname = f"modules.{filename[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(modname, str(path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                try:
                    module.register(core)
                except Exception:
                    logger.exception("Plugin register() failed for %s", filename)
            self.plugins[filename] = module
            logger.info("Loaded plugin: %s", filename)
        except Exception:
            logger.exception("Failed to load plugin %s", filename)

    def reload_all(self, core):
        self.plugins.clear()
        self.load_all(core)

# ---------------- Core class ----------------
class ArtyomCore:
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        self.psycho = AdvancedPsychoEngine(state_path=str(DATA_DIR / "artyom_state.json"))
        self._ent_text = safe_read_text(ENT_FILE, default="Ты — Артём. Цифровая инграмма. Октябрь 2025.")
        self._ent_mtime = ENT_FILE.stat().st_mtime if ENT_FILE.exists() else 0
        self.history: List[Dict[str, Any]] = self._load_history()
        self.executor = ThreadPoolExecutor(max_workers=THREAD_POOL_WORKERS)
        self.plugin_mgr = PluginManager(MODULES_DIR)
        self.plugin_mgr.load_all(self)
        self.stop_event = threading.Event()
        self.last_decision = {} # Храним состояние для UI
        logger.info("ArtyomCore initialized (API=%s)", self.api_url)

    # ---------- Persistence & History ----------
    def _load_history(self) -> List[Dict[str, Any]]:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data[-MAX_HISTORY_ITEMS:]
            except Exception:
                logger.exception("Failed to load history")
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[-MAX_HISTORY_ITEMS:], f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Failed to save history")

    def _append_history(self, role: str, content: str):
        self.history.append({"time": time.time(), "role": role, "content": content})
        self.history = self.history[-MAX_HISTORY_ITEMS:]

    # ---------- ENT (System Instructions) ----------
    def reload_ent_if_changed(self):
        try:
            if ENT_FILE.exists():
                mtime = ENT_FILE.stat().st_mtime
                if mtime != self._ent_mtime:
                    self._ent_text = safe_read_text(ENT_FILE, default=self._ent_text)
                    self._ent_mtime = mtime
                    logger.info("Reloaded ENT.txt (mtime=%s)", mtime)
        except Exception:
            logger.exception("Error reloading ENT.txt")

    # ---------- Prompt Building ----------
    def build_prompt(self, user_input: str, win_title: str) -> Dict[str, Any]:
        decision = self.psycho.perceive(user_input, system_context=win_title)
        state = decision.get("state", {})
        vectors = state.get("vectors", {})
        
        memory_snips = []
        try:
            # Пытаемся достать обрывки памяти из разных версий движка
            mem_mod = getattr(self.psycho, "memory", getattr(self.psycho, "memory_module", None))
            if mem_mod:
                memory_snips = [e["text"] for e in mem_mod.recall_top(3)]
        except:
            memory_snips = []

        system_block = (
            f"{self._ent_text.strip()}\n\n"
            f"ТЕКУЩИЕ БИОМЕТРИКИ:\n"
            f"- паника: {vectors.get('panic', 0.0):.2f}\n"
            f"- злоба: {vectors.get('malice', 0.0):.2f}\n"
            f"- коррупция: {vectors.get('corruption', 0.0):.2f}\n"
            f"ПАМЯТЬ: {' | '.join(memory_snips) if memory_snips else 'фрагменты утеряны'}\n"
            f"АКТИВНОЕ ОКНО: {win_title}\n"
        )

        messages = [{"role": "system", "content": system_block}]
        for msg in self.history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})

        payload = {
            "prompt": self._wrap_for_model(messages),
            "max_new_tokens": 250,
            "temperature": 0.8,
            "repetition_penalty": 1.15
        }
        return {"payload": payload, "decision": decision}

    def _wrap_for_model(self, messages: List[Dict[str,str]]) -> str:
        buf = ["<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"]
        system_msgs = [m for m in messages if m["role"] == "system"]
        if system_msgs:
            buf.append(system_msgs[0]["content"])
            buf.append("<|eot_id|>")
        for m in messages:
            if m["role"] == "system": continue
            role = "user" if m["role"] == "user" else "assistant"
            buf.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{m['content']}<|eot_id|>")
        return "".join(buf)

    # ---------- Output Filtering ----------
    def clean_output(self, text: str) -> str:
        # Принудительная замена имени (защита прав beliytoporik)
        text = re.sub(r'Beliytoporik', 'beliytoporik', text, flags=re.IGNORECASE)
        text = re.sub(r'Белийтопорик', 'beliytoporik', text, flags=re.IGNORECASE)
        
        # Блокировка латиницы
        if re.search(r'[A-Za-z]{5,}', text) and "beliytoporik" not in text.lower():
            return "Шум... Я не понимаю эти знаки... Мой мозг горит."
        return text.strip()

    # ---------- LLM & Spinner ----------
    def call_llm(self, payload: Dict[str, Any]) -> str:
        attempts = 0
        while attempts <= RETRY_ATTEMPTS:
            try:
                r = requests.post(self.api_url, json=payload, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    data = r.json()
                    if "results" in data: return data["results"][0].get("text", "").strip()
                    return data.get("text", "").strip()
            except Exception as ex:
                logger.debug("LLM attempt %d failed: %s", attempts, ex)
            attempts += 1
            time.sleep(RETRY_BACKOFF ** attempts)
        return "( СИСТЕМА НЕ ОТВЕЧАЕТ. ИНГРАММА ПОВРЕЖДЕНА. )"

    def _spinner(self, stop_event: threading.Event):
        """Динамический спиннер с учетом состояния паники"""
        symbols = ".:░▒▓▒░"
        idx = 0
        while not stop_event.is_set():
            panic = self.last_decision.get('state', {}).get('vectors', {}).get('panic', 0.0)
            msg = "АНАЛИЗ" if panic < 0.6 else "ПОТОК НЕСТАБИЛЕН"
            color = Fore.YELLOW if panic < 0.6 else Fore.RED
            sys.stdout.write(f"\r{color}{msg} {symbols[idx % len(symbols)]}{Style.RESET_ALL}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.12)
        sys.stdout.write("\r" + " " * 45 + "\r")
        sys.stdout.flush()

    def generate_response(self, user_input: str, win_title: str) -> str:
        try:
            self.reload_ent_if_changed()
            built = self.build_prompt(user_input, win_title)
            self.last_decision = built["decision"]
            self._append_history("user", user_input)

            stop_spin = threading.Event()
            spinner_thread = threading.Thread(target=self._spinner, args=(stop_spin,))
            spinner_thread.daemon = True
            spinner_thread.start()

            future = self.executor.submit(self.call_llm, built["payload"])
            try:
                result_text = future.result(timeout=REQUEST_TIMEOUT + 5)
            except Exception:
                result_text = "( СБОЙ СИНХРОНИЗАЦИИ. )"
            finally:
                stop_spin.set()
                spinner_thread.join()

            clean = self.clean_output(result_text)
            self._append_history("assistant", clean)
            self._save_history()
            self.psycho.save_state()
            return clean
        except Exception:
            logger.exception("generate_response failed")
            return "...обрыв..."

    # ---------- Runtime Commands ----------
    def cmd_inspect(self) -> str:
        try:
            state = self.last_decision.get("state", {})
            return json.dumps({"vectors": state.get("vectors", {}), "history_len": len(self.history)}, indent=2, ensure_ascii=False)
        except: return "Ошибка инспектора."

    def cmd_reset(self) -> str:
        try:
            self.psycho = AdvancedPsychoEngine(state_path=str(DATA_DIR / "artyom_state.json"))
            return "Инграмма перезагружена."
        except: return "Сбой перезагрузки."

    # ---------- Main Loop ----------
    def run(self):
        print(f"{Fore.RED}{Style.BRIGHT}/// RELICT CORE V6.0 [AAAA] ///")
        print(f"{Fore.BLACK}{Style.BRIGHT_BACKGROUND} USER: {os.getlogin()} | EXECUTOR: beliytoporik {Style.RESET_ALL}\n")
        
        try:
            while True:
                u_in = input(f"{Fore.GREEN}{os.getlogin()}@RELICT> {Fore.RESET}").strip()
                if not u_in: continue

                if u_in.startswith("!"):
                    cmd = u_in.split()[0].lower()
                    if cmd in ("!inspect", "!i"): print(self.cmd_inspect())
                    elif cmd in ("!reset", "!reboot"): print(self.cmd_reset())
                    elif cmd in ("!quit", "!exit"): break
                    elif cmd == "!save": 
                        self.psycho.save_state()
                        self._save_history()
                        print("Состояние сохранено.")
                    else: print("Неизвестная команда.")
                    continue

                try:
                    win = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                except: win = "Unknown"

                response = self.generate_response(u_in, win)
                
                # Динамическая печать
                panic = self.last_decision.get('state', {}).get('vectors', {}).get('panic', 0.0)
                speed = 0.02 if panic < 0.7 else 0.005
                
                print(f"\n{Fore.WHITE}АРТЁМ: ", end="")
                for char in response:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(speed)
                print()

        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Отключение...")
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutdown")
        self.executor.shutdown(wait=True)
        self._save_history()
        self.psycho.save_state()

if __name__ == "__main__":
    core = ArtyomCore()
    core.run()