import os
import time
import pyautogui
from PIL import Image, ImageFilter

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("corruption", 0) > 0.8:
        # Артем "фотографирует" твой экран и портит его
        screenshot = pyautogui.screenshot()
        # Накладываем эффект размытия и инверсии
        distorted = screenshot.filter(ImageFilter.GaussianBlur(radius=5))
        distorted = distorted.point(lambda p: 255 - p) 
        
        save_path = os.path.join(core.data_dir, "vision_glitch.png")
        distorted.save(save_path)
        os.startfile(save_path) # Мгновенно открываем