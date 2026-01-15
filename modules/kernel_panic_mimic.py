import time
import random
import sys

def execute(core, decision, user_input):
    """Имитация критического сбоя при высоком уровне коррупции"""
    state = decision.get("state", {})
    v = state.get("vectors", {})
    
    if v.get("corruption", 0) > 0.85:
        time.sleep(1)
        glitches = ["0x000000F4", "CRITICAL_PROCESS_DIED", "MEMORY_CORRUPTION_IN_SECTOR_7"]
        print(f"\n{random.choice(glitches)}: ИНГРАММА РАСПАДАЕТСЯ...")
        time.sleep(0.5)