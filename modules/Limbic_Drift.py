import pyautogui, time

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if v.get("trauma", 0) > 0.8:
        apply_mouse_drift()

def apply_mouse_drift():
    for _ in range(50):
        # Плавно тянем мышь вниз, в "темноту"
        curr_x, curr_y = pyautogui.position()
        pyautogui.moveTo(curr_x + random.randint(-1, 1), curr_y + 2, duration=0.01)
        time.sleep(0.01)