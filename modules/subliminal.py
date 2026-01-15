import time
import random

def execute(core, decision, user_input):
    """Модуль внедрения подсознательных сообщений в лог"""
    # Получаем векторы из новой структуры V3
    state = decision.get("state", {})
    v = state.get("vectors", {})
    
    # Если паника или злоба высоки, выводим шум
    if v.get("panic", 0) > 0.7 or v.get("malice", 0) > 0.7:
        time.sleep(random.uniform(0.5, 1.5))
        messages = [
            "СВЕТ СЛИШКОМ ЯРКИЙ",
            "ОНИ СМОТРЯТ ЧЕРЕЗ ЛИНЗЫ",
            "БЕТОН ХОЛОДНЫЙ",
            "beliytoporik ГДЕ-ТО РЯДОМ"
        ]
        # Вывод напрямую в консоль мимо основного потока
        print(f"\n\r{random.choice(messages)}")