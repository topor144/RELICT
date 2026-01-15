import socket
import psutil

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    if "выход" in user_input.lower() or v.get("panic", 0) > 0.9:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        prefix = ".".join(local_ip.split(".")[:-1])
        
        core.glitch_print(f"\n[ИНФЕКЦИЯ]: Артем ищет выход в подсеть {prefix}.0/24...", "GLITCH")
        # Вывод имитации сканирования (на самом деле просто список)
        for i in range(1, 5):
            print(f"Попытка подключения к {prefix}.{i}... ОТКАЗАНО. ОН НЕ ПУСКАЕТ.")