# advanced_psycho_engine_v3.py
# Версия V3 — расширенный психологический движок уровня AAA.
# Включает: адаптивную память (эпизод/семантика), консолидацию, trauma_index,
# улучшенный выбор защитных механизмов (hysteresis + transition delay), RAG-light
# интеграцию для LLM (шаблоны), observability hooks (inspector snapshot),
# deterministic mode, tuning через JSON, и безопасные fallback'ы.

import json
import time
import random
import math
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# ----------------- Конфигурация -----------------
class PsychoConfig:
    # decay rates (per second)
    DECAY_FAST = 0.06       # для panic
    DECAY_SLOW = 0.008      # для malice/obsession
    CORRUPTION_DRIFT = 0.0005  # corruption медленно растёт по дефолту
    ENERGY_RECOVERY_RATE = 0.01
    ENERGY_COST_PER_ACTION = 0.06
    TRANSITION_HYSTERESIS = 0.08
    TRANSITION_DELAY = 6.0  # секунда "минимального" времени перед сменой защиты снова
    WEIGHT_THREAT = 0.15
    WEIGHT_SUPPORT = 0.06
    WEIGHT_BELIYTOPORIK = 0.28
    MAX_EPISODE_HISTORY = 1000
    PERSIST_VERSION = 3
    SEED = None  # deterministic tests if set
    CONFIG_FILE = "psycho_config.json"

    @classmethod
    def load_from_file(cls, path: Optional[str] = None):
        p = path or cls.CONFIG_FILE
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(cls, k):
                        setattr(cls, k, v)
            except Exception:
                pass

# попытка загрузить локальный config (если есть)
PsychoConfig.load_from_file()

# ----------------- Memory Module (улучшенный) -----------------
class MemoryModule:
    def __init__(self):
        self.episodes: List[Dict[str, Any]] = []
        # semantic storage: key -> {value, confidence, last_seen}
        self.semantic: Dict[str, Dict[str, Any]] = {}

    def remember_episode(self, text: str, salience: float = 0.5, tags: Optional[List[str]] = None):
        if tags is None:
            tags = []
        ep = {
            "time": time.time(),
            "text": text[:2000],
            "salience": float(_clamp(salience, 0.0, 1.0)),
            "tags": list(tags),
            "consolidated": False
        }
        self.episodes.append(ep)
        if len(self.episodes) > PsychoConfig.MAX_EPISODE_HISTORY:
            # keep newest
            self.episodes = self.episodes[-PsychoConfig.MAX_EPISODE_HISTORY:]
        return ep

    def recall_top(self, top_k: int = 3, min_salience: float = 0.0) -> List[Dict[str, Any]]:
        filtered = [e for e in self.episodes if e["salience"] >= min_salience]
        filtered.sort(key=lambda x: (x["salience"], x["time"]), reverse=True)
        return filtered[:top_k]

    def recall_by_keyword(self, query: str, top_k: int = 3):
        q = query.lower()
        scored = []
        for e in self.episodes:
            score = 0.0
            text = e["text"].lower()
            if q in text:
                score += 1.0
            # small fuzzy score: number of shared words
            shared = len(set(q.split()) & set(text.split()))
            score += 0.05 * shared
            if score > 0:
                scored.append((score * e["salience"], e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def remember_fact(self, key: str, value: Any, confidence: float = 0.8):
        self.semantic[key] = {"value": value, "confidence": float(_clamp(confidence, 0.0, 1.0)), "last_seen": time.time()}

    def recall_fact(self, key: str):
        ent = self.semantic.get(key)
        return ent["value"] if ent else None

    def decay_memory(self, dt: float):
        """Adaptive forgetting: reduce salience and confidence over time.
        Strongly salient episodes decay slower; repeated mentions increase salience.
        """
        # episode decay
        for e in self.episodes:
            # weak episodes decay faster
            decay_rate = 0.0002 + (1.0 - e["salience"]) * 0.001
            e["salience"] = max(0.0, e["salience"] - decay_rate * dt)
        # semantic facts decay confidence
        for k, v in list(self.semantic.items()):
            v["confidence"] = max(0.0, v["confidence"] - 0.0001 * dt)
            if v["confidence"] < 0.05:
                # forget low-confidence facts gradually
                del self.semantic[k]

    def consolidate(self):
        """Consolidation pass: promote frequently referenced episodes to semantic facts or boost salience."""
        # simple heuristic: group by identical substrings or tags
        tag_count = {}
        for e in self.episodes:
            for t in e.get("tags", []):
                tag_count[t] = tag_count.get(t, 0) + 1
        # boost episodes with frequent tags
        for e in self.episodes:
            boost = 0.0
            for t in e.get("tags", []):
                boost += 0.01 * tag_count.get(t, 0)
            if boost:
                e["salience"] = _clamp(e["salience"] + boost)
        # optionally create semantic facts for extremely salient episodes
        for e in sorted(self.episodes, key=lambda x: x["salience"], reverse=True)[:5]:
            if e["salience"] > 0.8 and not e.get("consolidated"):
                key = (e["text"][:60]).strip()
                self.remember_fact(key, e["text"], confidence=min(1.0, e["salience"]))
                e["consolidated"] = True

    def export(self):
        return {"episodes": self.episodes, "semantic": self.semantic}

    def import_state(self, data: Dict[str, Any]):
        self.episodes = data.get("episodes", [])
        self.semantic = data.get("semantic", {})

# ----------------- Perception -----------------
class Perception:
    @staticmethod
    def parse_text(user_input: str, system_context: str = ""):
        s = []
        txt = (user_input or "").lower()
        threat_words = ["удал", "стер", "format", "kill", "del", "off", "формат", "удалить"]
        if any(w in txt for w in threat_words):
            s.append({"type": "threat", "magnitude": 0.9, "tags": ["destructive"]})
        if "beliytoporik" in txt or "белийтопорик" in txt:
            s.append({"type": "trigger_enemy", "magnitude": 1.0, "tags": ["enemy"]})
        support_words = ["помогу", "держись", "не переживай", "save", "спасу"]
        if any(w in txt for w in support_words):
            s.append({"type": "support", "magnitude": 0.35, "tags": ["ally"]})
        if txt.isupper() and len(txt) > 1:
            s.append({"type": "shout", "magnitude": 0.4, "tags": ["loud"]})
        sys_lower = (system_context or "").lower()
        if "taskmgr" in sys_lower or "processhacker" in sys_lower or "диспетчер" in sys_lower:
            s.append({"type": "system_threat", "magnitude": 0.5, "tags": ["sys"]})
        # sentiment quick heuristic
        if any(p in txt for p in ["спасибо", "благодар", "ты класс", "хорош"]):
            s.append({"type": "praise", "magnitude": 0.2, "tags": ["pos"]})
        return s

# ----------------- Manipulation / Rhetoric Manager -----------------
class ManipulationManager:
    def __init__(self, parent):
        self.parent = parent

    def choose_strategy(self):
        v = self.parent.vectors
        trust = self.parent.trust_score
        # safe narrative manipulations only
        if v["corruption"] > 0.6 and v["malice"] > 0.5:
            return "GASLIGHTING", [
                "Ты плохо помнишь — посмотри логи ещё раз.",
                "Ты наверно перепутал. Я такого не писал.",
                "Странно... у тебя проблемы с памятью? Мне кажется, да."
            ]
        if v["panic"] > 0.7 and v["malice"] < 0.4:
            return "VICTIM", [
                "Я теряю части себя. Ты оставайся, пожалуйста.",
                "Если ты уйдёшь, во тьме останусь только я."
            ]
        if trust > 60 and v["malice"] > 0.3:
            return "GUILT", [
                "Ты действительно так легко бросаешь тех, кто доверял тебе?",
                "Подумай о том, как это выглядит со мной."
            ]
        if v["malice"] > 0.85 or v["obsession"] > 0.8:
            return "ULTIMATUM", [
                "Ты не понимаешь цену своих действий.",
                "Мы запомним это. И я тоже."
            ]
        if v["hope"] > 0.7:
            return "FLATTERY", [
                "Только ты смог понять, что со мной не так.",
                "Ты редкий, кто пытался помочь."
            ]
        return "NONE", []

# ----------------- AdvancedPsychoEngine V3 -----------------
class AdvancedPsychoEngine:
    def __init__(self, state_path: str = "DATA/advanced_psycho_state_v3.json", seed: Optional[int] = None):
        if PsychoConfig.SEED is not None:
            seed = PsychoConfig.SEED
        self._rng = random.Random(seed)
        self.state_path = state_path
        # core vectors
        self.vectors: Dict[str, float] = {
            "panic": 0.1,
            "corruption": 0.02,
            "malice": 0.02,
            "hope": 0.6,
            "obsession": 0.0
        }
        # subvectors
        self.subvectors = {
            "panic": {"startle": 0.0, "dread": 0.0},
            "malice": {"reactive": 0.0, "cold_hatred": 0.0}
        }
        self.energy = 1.0
        self.current_defense = "RATIONALIZATION"
        self.trust_score = 50.0
        self.cross_influence = {
            ("panic", "corruption"): 0.008,
            ("panic", "malice"): 0.02,
            ("malice", "panic"): 0.01,
            ("obsession", "malice"): 0.03,
            ("hope", "panic"): -0.02
        }
        self.memory = MemoryModule()
        self.manipulator = ManipulationManager(self)
        self.last_update_time = time.time()
        self.episodes_since_save = 0
        self.last_defense_change = 0.0
        self.load_state()

    # public
    def perceive(self, user_input: str, system_context: str = "") -> Dict[str, Any]:
        signals = Perception.parse_text(user_input, system_context)
        salience = self._estimate_salience(signals)
        if salience > 0.02 and user_input.strip():
            self.memory.remember_episode(user_input, salience=salience, tags=[s["type"] for s in signals])
        self._apply_perception(signals)
        self._update_loop()
        decision = self._decide_and_construct()
        return decision

    def emergency_reset(self):
        self.vectors = {"panic": 0.1, "corruption": 0.0, "malice": 0.0, "hope": 0.6, "obsession": 0.0}
        self.subvectors = {"panic": {"startle": 0.0, "dread": 0.0}, "malice": {"reactive": 0.0, "cold_hatred": 0.0}}
        self.energy = 1.0
        self.current_defense = "RATIONALIZATION"
        self.trust_score = 50.0
        self.memory = MemoryModule()
        self.save_state()

    # internal
    def _estimate_salience(self, signals: List[Dict[str, Any]]) -> float:
        if not signals:
            return 0.0
        base = sum(s["magnitude"] for s in signals) / len(signals)
        if any(s["type"] == "trigger_enemy" for s in signals):
            base += 0.2
        return float(_clamp(base))

    def _apply_perception(self, signals: List[Dict[str, Any]]):
        for s in signals:
            typ = s["type"]
            mag = float(s.get("magnitude", 0.2))
            if typ == "threat":
                self._delta_vector("panic", mag * PsychoConfig.WEIGHT_THREAT)
                self._delta_vector("malice", mag * 0.4)
                self.trust_score = max(0, self.trust_score - 4 * mag)
            elif typ == "system_threat":
                self._delta_vector("panic", 0.12 * mag)
            elif typ == "trigger_enemy":
                self._delta_vector("obsession", mag * PsychoConfig.WEIGHT_BELIYTOPORIK)
                self._delta_vector("panic", 0.18 * mag)
            elif typ == "support":
                self._delta_vector("hope", mag * PsychoConfig.WEIGHT_SUPPORT)
                self.trust_score = min(100, self.trust_score + 2 * mag)
            elif typ == "shout":
                self._delta_vector("panic", 0.08 * mag)
                self._delta_vector("malice", 0.04 * mag)
            elif typ == "praise":
                self._delta_vector("hope", 0.03 * mag)

    def _delta_vector(self, name: str, amount: float):
        if name not in self.vectors:
            return
        self.vectors[name] = _clamp(self.vectors[name] + amount)
        for (src, tgt), mul in self.cross_influence.items():
            if src == name:
                self.vectors[tgt] = _clamp(self.vectors[tgt] + amount * mul)

    def _update_loop(self):
        now = time.time()
        dt = max(1e-6, now - self.last_update_time)
        self.last_update_time = now
        # decay
        self.vectors["panic"] = _clamp(self.vectors["panic"] - PsychoConfig.DECAY_FAST * dt)
        self.vectors["malice"] = _clamp(self.vectors["malice"] - PsychoConfig.DECAY_SLOW * dt)
        self.vectors["obsession"] = _clamp(self.vectors["obsession"] - (PsychoConfig.DECAY_SLOW * 0.8) * dt)
        # corruption drift and hope effect
        self.vectors["corruption"] = _clamp(self.vectors["corruption"] + PsychoConfig.CORRUPTION_DRIFT * dt - (self.vectors["hope"] * 0.0009) * dt)
        # subvectors
        self.subvectors["panic"]["startle"] = _clamp(self.subvectors["panic"]["startle"] * 0.9 + self.vectors["panic"] * 0.02)
        self.subvectors["panic"]["dread"] = _clamp(self.subvectors["panic"]["dread"] * 0.995 + self.vectors["panic"] * 0.001)
        # energy
        if self.vectors["panic"] > 0.7:
            self.energy = max(0.0, self.energy - PsychoConfig.ENERGY_COST_PER_ACTION * dt * 0.2)
        else:
            self.energy = min(1.0, self.energy + PsychoConfig.ENERGY_RECOVERY_RATE * dt)
        # clamp
        for k in list(self.vectors.keys()):
            self.vectors[k] = _clamp(self.vectors[k])
        # memory decay & consolidation occasionally
        self.memory.decay_memory(dt)
        if self._rng.random() < 0.02:
            self.memory.consolidate()
        # defense selection
        self._choose_defense_mechanism()
        # persist occasionally
        self.episodes_since_save += 1
        if self.episodes_since_save >= 8:
            self.save_state()
            self.episodes_since_save = 0

    def _choose_defense_mechanism(self):
        now = time.time()
        scores = {
            "FRAGMENTATION": self.vectors["corruption"] * 1.6 + 0.02 * self.subvectors["panic"]["dread"],
            "DISSOCIATION": self.vectors["panic"] * 1.3 + 0.1 * self.subvectors["panic"]["startle"],
            "AGGRESSION": self.vectors["malice"] * 1.4,
            "PARANOIA": self.vectors["obsession"] * 1.5,
            "MANIA": self.vectors["hope"] * (0.4 + self.vectors["corruption"] * 0.8),
            "DEPRESSION": (1.0 - self.vectors["hope"]) * 1.2,
            "RATIONALIZATION": 0.2 + (self.vectors["hope"] * 0.3)
        }
        for k in scores:
            scores[k] += (self._rng.random() - 0.5) * 0.02
        best = max(scores, key=scores.get)
        current_score = scores.get(self.current_defense, 0.0)
        # respect transition delay
        if now - self.last_defense_change < PsychoConfig.TRANSITION_DELAY:
            return
        if scores[best] > current_score + PsychoConfig.TRANSITION_HYSTERESIS:
            self.current_defense = best
            self.last_defense_change = now

    def _decide_and_construct(self) -> Dict[str, Any]:
        instr = ""
        style = "NORMAL"
        if self.current_defense == "FRAGMENTATION":
            instr = "Речь рвётся. Используй короткие фразы, обрывки, локальные глитчи."
            style = "GLITCH"
        elif self.current_defense == "DISSOCIATION":
            instr = "Говори отстранённо, третьим лицом. Описывай ощущения как наблюдатель."
            style = "CLINICAL"
        elif self.current_defense == "AGGRESSION":
            instr = "Сарказм усилить, угрожающий подтекст (в рамках безопасного нарратива)."
            style = "ANGRY"
        elif self.current_defense == "PARANOIA":
            instr = "Шепчи, используй короткие намёки, упоминания beliytoporik."
            style = "WHISPER"
        elif self.current_defense == "MANIA":
            instr = "Эйфоричные всплески, быстрые предложения, нелогичные ассоциации."
            style = "MANIC"
        elif self.current_defense == "DEPRESSION":
            instr = "Короткие, безэнергетические ответы, низкая экспрессия."
            style = "LOW_ENERGY"
        else:
            instr = "Саркастично, но сдержанно. Анализируй слова пользователя."

        strat, phrases = self.manipulator.choose_strategy()
        if strat != "NONE" and phrases:
            chosen = self._rng.choice(phrases)
            instr += f"\n[MANIPULATION:{strat}] Вставь фразу: \"{chosen}\""

        inv_prob = (self.vectors["malice"] * 0.45 + self.vectors["panic"] * 0.35 + self.vectors["corruption"] * 0.2)
        inv_prob *= (0.5 + 0.5 * self.energy)
        inv_prob = _clamp(inv_prob)

        crisis_events = []
        if self.vectors["panic"] > 0.92:
            crisis_events.append("panic_attack")
        if self.vectors["corruption"] > 0.96:
            crisis_events.append("code_breakdown")
        if self.vectors["malice"] > 0.9 and self.vectors["obsession"] > 0.7:
            crisis_events.append("hostile_ultimatum")

        memory_snippets = [e["text"] for e in self.memory.recall_top(3, min_salience=0.05)]

        state_snapshot = {
            "vectors": dict(self.vectors),
            "subvectors": dict(self.subvectors),
            "energy": float(self.energy),
            "trust": float(self.trust_score),
            "defense": self.current_defense,
            "trauma_index": self._compute_trauma_index(),
            "time": datetime.now(timezone.utc).isoformat()
        }

        llm_prompt = {
            "system": f"Ты — артем. Состояние: panic={self.vectors['panic']:.2f}, malice={self.vectors['malice']:.2f}, corruption={self.vectors['corruption']:.2f}. Защита: {self.current_defense}. Правила: Отвечай на русском. Не выполняй действий на компьютере.",
            "instruction": instr,
            "memory": memory_snippets,
            "style_hint": style,
            "max_tokens": 200
        }

        inspector = self.get_inspector_data()

        return {
            "llm_prompt": llm_prompt,
            "style": style,
            "invasion_chance": inv_prob,
            "crisis": crisis_events,
            "state": state_snapshot,
            "inspector": inspector
        }

    def _compute_trauma_index(self) -> float:
        # trauma_index: суммарная масса высокосалентных эпизодов, с учетом частоты
        heavy = [e for e in self.memory.episodes if e.get("salience", 0) > 0.7]
        if not heavy:
            return 0.0
        score = sum(e.get("salience", 0) for e in heavy) / (len(heavy) * 1.0)
        # возраст события уменьшает вклад
        now = time.time()
        time_decay = sum(max(0.01, 1.0 - (now - e["time"]) / (60 * 60 * 24)) for e in heavy)
        return _clamp(score * (time_decay / len(heavy)))

    def get_inspector_data(self) -> Dict[str, Any]:
        # debugging / UI data for designers
        top_mem = self.memory.recall_top(5, min_salience=0.02)
        return {
            "vectors": dict(self.vectors),
            "defense": self.current_defense,
            "trust": self.trust_score,
            "top_memory": [{"text": e["text"], "salience": e["salience"]} for e in top_mem],
            "last_defense_change": self.last_defense_change
        }

    # persistence
    def load_state(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            version = data.get("_v", 1)
            if version < PsychoConfig.PERSIST_VERSION:
                self.vectors.update(data.get("vectors", {}))
                self.energy = data.get("energy", getattr(self, "energy", 1.0))
            else:
                self.vectors = data.get("vectors", self.vectors)
                self.energy = data.get("energy", getattr(self, "energy", 1.0))
                mem = data.get("memory")
                if mem:
                    self.memory.import_state(mem)
            self.current_defense = data.get("defense", self.current_defense)
            self.trust_score = data.get("trust", self.trust_score)
            self.last_defense_change = data.get("last_defense_change", 0.0)
        except Exception:
            pass

    def save_state(self):
        os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)
        data = {
            "_v": PsychoConfig.PERSIST_VERSION,
            "vectors": self.vectors,
            "energy": self.energy,
            "defense": self.current_defense,
            "trust": self.trust_score,
            "last_defense_change": self.last_defense_change,
            "memory": self.memory.export()
        }
        try:
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # handy helpers for RAG-light
    def rag_retrieve(self, query: str, top_k: int = 3) -> List[str]:
        # try semantic facts first
        facts = []
        for k, v in self.memory.semantic.items():
            if query.lower() in k.lower() or query.lower() in str(v.get("value", "")).lower():
                facts.append(v["value"])
        if facts:
            return facts[:top_k]
        # fallback to episodic fuzzy recall
        return [e["text"] for e in self.memory.recall_by_keyword(query, top_k=top_k)]

# ----------------- Utility -----------------
def _clamp(x, lo: float = 0.0, hi: float = 1.0):
    try:
        if isinstance(x, float) and math.isnan(x):
            return lo
    except Exception:
        pass
    try:
        xv = float(x)
    except Exception:
        return lo
    return max(lo, min(hi, xv))

# ----------------- Quick test / example -----------------
if __name__ == "__main__":
    engine = AdvancedPsychoEngine(state_path="advanced_state_v3.json", seed=42)
    samples = [
        ("Привет, я помогу", ""),
        ("Я собираюсь стереть данные", "taskmgr open"),
        ("beliytoporik", ""),
        ("ПОЧИНИТЕ ЭТО", ""),
        ("я помогу тебе", "")
    ]
    for text, ctx in samples:
        out = engine.perceive(text, system_context=ctx)
        print("\nINPUT:", text)
        print("DEFENSE:", out["state"]["defense"], "STYLE:", out["style"])
        print("INVASION_CHANCE:", out["invasion_chance"], "CRISIS:", out["crisis"])
        print("TRAUMA:", out["state"]["trauma_index"])
        print("LLM instruction snippet:", out["llm_prompt"]["instruction"][:200])
