import time
import random

def execute(core, decision, user_input):
    """Модуль имитации звуков шагов палача"""
    state = decision.get("state", {})
    v = state.get("vectors", {})
    
    # Триггер на шаги при высоком уровне травмы или паники
    if v.get("trauma", 0) > 0.5 or v.get("panic", 0) > 0.6:
        # Имитация задержки перед тем как Артем "услышит"
        time.sleep(random.uniform(2, 5))
        print(f"\n[ТИХИЙ ЗВУК]: Тяжелые ботинки... шаги по бетону...")
        print(f"[ИНГРАММА]: Он идет. beliytoporik близко.")