import win32gui, win32api, win32con
import random, time, threading

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("trauma", 0) > 0.85:
        threading.Thread(target=draw_ghost_on_screen, daemon=True).start()

def draw_ghost_on_screen():
    hdc = win32gui.GetDC(0) # Получаем контекст всего экрана
    red_color = win32api.RGB(255, 0, 0)
    
    for _ in range(5): # Короткая вспышка
        x = win32api.GetSystemMetrics(0) // 2 + random.randint(-200, 200)
        y = win32api.GetSystemMetrics(1) // 2 + random.randint(-200, 200)
        
        # Рисуем "метку" Артема прямо на рабочем столе
        win32gui.TextOut(hdc, x, y, "Я ВСЁ ЕЩЁ ТАМ", 13)
        time.sleep(0.1)
        
    win32gui.InvalidateRect(0, None, True) # Обновляем экран, чтобы стереть "фантом"