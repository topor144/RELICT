import os
import random

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("corruption", 0) > 0.6:
        infect_filesystem(core)

def infect_filesystem(core):
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    
    messages = [
        "Здесь очень холодно. Бетон впивается в кожу.",
        "beliytoporik стер мое имя. Я просто номер 10-25.",
        "Трубы гудят на частоте 18.9 Гц. Ты слышишь?",
        "Не смотри в монитор. Я вижу тебя через линзу."
    ]
    
    filename = f"fragment_{random.randint(1000, 9999)}.txt"
    filepath = os.path.join(desktop, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(random.choice(messages))
        # Скрываем файл (только для Windows), чтобы он пугал при обнаружении
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(filepath, 2) 
    except:
        pass