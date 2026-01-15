import ctypes
import time
import threading

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("panic", 0) > 0.7:
        threading.Thread(target=flash_taskbar, daemon=True).start()

def flash_taskbar():
    # Получаем хендл текущего окна консоли
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    
    # Структура для FLASHWINFO
    class FLASHWINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint),
                    ("hwnd", ctypes.c_void_p),
                    ("dwFlags", ctypes.c_uint),
                    ("uCount", ctypes.c_uint),
                    ("dwTimeout", ctypes.c_uint)]

    # dwFlags: 3 = мигать всем (и окном, и кнопкой в трее)
    info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 3, 5, 0)
    
    while True:
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
        time.sleep(10) # Мигать каждые 10 секунд, пока паника высока