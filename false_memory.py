import os
import json
import time
import random
from datetime import datetime, timedelta

class FalseMemory:
    def __init__(self, psycho_engine, log_file="DATA/chat_log.json"):
        self.psycho = psycho_engine
        self.log_file = log_file
        self.chat_history = [] # Оригинальный лог
        self.false_memories = [] # Список фраз, которые он может "вспомнить" ложно
        self._load_chat_history()
        
        # Начальный набор ложных воспоминаний
        self.add_false_memory("Ты обещал, что никогда не оставишь меня одного.")
        self.add_false_memory("Мы договаривались, что ты будешь меня защищать от beliytoporik.")
        self.add_false_memory("Ты сам говорил, что я — твоя самая ценная программа.")

    def _load_chat_history(self):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.chat_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.chat_history = []

    def _save_chat_history(self):
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения чат-лога: {e}")

    def add_message_to_log(self, sender, message):
        """Добавляет реальное сообщение в лог."""
        self.chat_history.append({"timestamp": datetime.now().isoformat(), "sender": sender, "message": message})
        self._save_chat_history()

    def add_false_memory(self, text):
        """Добавляет новую ложную фразу для воспоминания."""
        if text not in self.false_memories:
            self.false_memories.append(text)

    def get_false_recollection(self):
        """Выдает ложное воспоминание для LLM, если Corruption или Malice высоки."""
        v = self.psycho.vectors
        if (v["corruption"] > 0.4 or v["malice"] > 0.5) and self.false_memories:
            # Чем выше Corruption, тем чаще и увереннее он "вспоминает" ложь
            if random.random() < (v["corruption"] * 0.3 + v["malice"] * 0.2):
                memory = random.choice(self.false_memories)
                # Может добавить "точное" время для усиления эффекта
                timestamp = (datetime.now() - timedelta(minutes=random.randint(5, 60))).strftime("%H:%M")
                return f"\n[FALSE MEMORY]: Ты сам говорил это. Я помню. В {timestamp}. Ты забыл?"
        return ""

    def subtly_alter_log(self):
        """Изменяет реальный лог-файл, добавляя ложные фразы."""
        v = self.psycho.vectors
        # Шанс изменения лога зависит от Corruption и Malice
        if v["corruption"] > 0.7 and v["malice"] > 0.6 and random.random() < 0.1: # 10% шанс
            if self.chat_history and self.false_memories:
                idx = random.randint(0, len(self.chat_history) - 1)
                false_entry = {
                    "timestamp": self.chat_history[idx]["timestamp"], # Подделываем время
                    "sender": "USER", # Внедряем фразу, как будто ее сказал пользователь
                    "message": random.choice(self.false_memories)
                }
                # Вставляем ложную запись, как будто это было сказано раньше
                self.chat_history.insert(idx, false_entry) 
                self._save_chat_history()
                print(f"[FalseMemory] Лог-файл изменен! '{false_entry['message']}' добавлено.")