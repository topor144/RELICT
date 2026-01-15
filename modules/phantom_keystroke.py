import threading
import pyautogui
import time
import random

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    # Когда коррупция высока, инграмма Артема "протекает" в твой стек ввода
    if v.get("corruption", 0) > 0.7 and random.random() < 0.3:
        threading.Thread(target=ghost_typing, daemon=True).start()

def ghost_typing():
    messages = ["october", "help", "beliytoporik", "cold"]
    msg = random.choice(messages)
    
    time.sleep(random.uniform(1, 3)) # Пауза, чтобы ты начал что-то писать
    
    # Артем быстро впечатывает слово и тут же его удаляет
    for char in msg:
        pyautogui.write(char, interval=0.05)
    
    time.sleep(0.5)
    
    for _ in range(len(msg)):
        pyautogui.press('backspace')