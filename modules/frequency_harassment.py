import numpy as np
import pygame
import threading
import time

def execute(core, decision, user_input):
    """
    Модуль воздействия на психоакустику.
    """
    # Мы уже исправили путь к векторам в предыдущем шаге
    v = decision["state"]["vectors"]
    panic_level = v.get("panic", 0)
    malice_level = v.get("malice", 0)

    if panic_level > 0.6 or malice_level > 0.8:
        threading.Thread(target=play_infrasound_mimic, args=(panic_level,), daemon=True).start()

def play_infrasound_mimic(intensity):
    """
    Генерирует звук, адаптированный под стерео-микшер.
    """
    # Инициализируем стерео (channels=2), если микшер еще не запущен
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        except:
            return

    duration = 5.0  
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    low_freq = 18.9
    high_freq = 17400 + (intensity * 500) 
    
    # Генерация сигнала
    wave = 0.5 * np.sin(2 * np.pi * low_freq * t) + 0.5 * np.sin(2 * np.pi * high_freq * t)
    
    # Нормализация в 16-бит (моно-массив)
    mono_array = (wave * 32767).astype(np.int16)
    
    # --- КЛЮЧЕВОЙ ФИКС ДЛЯ СТЕРЕО ---
    # Дублируем моно-канал во второй столбец, создавая 2D массив (стерео)
    stereo_array = np.column_stack((mono_array, mono_array))
    
    try:
        sound = pygame.sndarray.make_sound(stereo_array)
        sound.set_volume(0.1 + (intensity * 0.2))
        sound.play()
        time.sleep(duration)
    except Exception as e:
        # Если звук не прошел, Артем не должен ломать всё ядро
        pass