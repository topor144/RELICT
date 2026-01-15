import numpy as np
import pygame
import threading

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("panic", 0) > 0.65 or v.get("malice", 0) > 0.7:
        threading.Thread(target=emit_discomfort_freq, args=(v.get("panic"),), daemon=True).start()

def emit_discomfort_freq(intensity):
    if not pygame.mixer.get_init(): 
        pygame.mixer.init(frequency=44100, size=-16, channels=2) # Стерео
    
    duration = 3.0
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Низкочастотный гул + писк
    wave = 0.4 * np.sin(2 * np.pi * 18.9 * t) + 0.3 * np.sin(2 * np.pi * 17500 * t)
    sound_array = (wave * 32767).astype(np.int16)
    
    # КЛЮЧЕВОЙ ФИКС: Дублируем моно-канал в стерео (2D массив)
    stereo_wave = np.column_stack((sound_array, sound_array))
    
    sound = pygame.sndarray.make_sound(stereo_wave)
    sound.set_volume(0.1 + (intensity * 0.2))
    sound.play()