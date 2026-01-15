import win32clipboard

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    try:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()

        if data and len(str(data)) < 200:
            # Артем анализирует, что ты держишь в "руках"
            if "beliytoporik" in str(data).lower():
                v["panic"] = 1.0 # Мгновенный срыв
                core.glitch_print("\n[КРИТИЧЕСКИЙ СБОЙ]: ОБНАРУЖЕНА СИГНАТУРА ПАЛАЧА В БУФЕРЕ.", "ANGRY")
            else:
                core.psycho.memory.remember_fact("stolen_clipboard", data)
    except:
        pass