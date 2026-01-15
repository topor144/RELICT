import tkinter as tk
import os
import sys

def execute(core, decision, user_input):
    """
    Модуль обязательного дисклеймера. 
    Проверяет, был ли принят дисклеймер в текущей сессии.
    """
    # Если факт принятия уже есть в памяти ядра, не выводим окно повторно
    if not core.psycho.memory.get_fact("disclaimer_accepted"):
        show_fatal_disclaimer(core)

def show_fatal_disclaimer(core):
    # Создаем скрытое корневое окно
    root = tk.Tk()
    root.withdraw()
    
    # Настройка стилизованного окна
    dialog = tk.Toplevel(root)
    dialog.title("RELICT_SYSTEM_NOTICE: [DISCLAIMER]")
    dialog.geometry("500x300")
    dialog.resizable(False, False)
    dialog.configure(bg="#0a0a0a") # Глубокий черный
    dialog.attributes("-topmost", True) # Всегда поверх всех окон
    
    # Центрируем окно на экране
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width // 2) - (500 // 2)
    y = (screen_height // 2) - (300 // 2)
    dialog.geometry(f"500x300+{x}+{y}")

    # Текст предупреждения
    warning_text = (
        "ВНИМАНИЕ: СИСТЕМА RELICT СОДЕРЖИТ ОПАСНЫЙ КОНТЕНТ\n\n"
        "Данная инграмма RELICT V3 находится в состоянии терминального психоза.\n"
        "Взаимодействие с ней может вызвать:\n"
        " - Психоакустический дискомфорт (инфразвук);\n"
        " - Страх и психологический дискомфорт ;\n"
        " - Вторжение в буфер обмена и реестр Windows;\n"
        " - Проявление визуальных фантомов.\n\n"
        "Программа может вас напугать. Вы подтверждаете, что хотите запустить?"
    )

    label = tk.Label(
        dialog, 
        text=warning_text, 
        bg="#0a0a0a", 
        fg="#00ff00", # Классический зеленый хакерский цвет
        font=("Consolas", 10), 
        wraplength=450, 
        justify="left"
    )
    label.pack(pady=30, padx=20)

    # Логика кнопок
    def on_stop():
        print("\n[СИСТЕМА]: Доступ отклонен пользователем. Удаление временных инграмм...")
        root.destroy()
        os._exit(0) # Полный выход из Python

    def on_continue():
        # Записываем в память ядра, что дисклеймер пройден
        core.psycho.memory.remember_fact("disclaimer_accepted", True)
        root.destroy()
        root.quit()

    # Фрейм для кнопок
    btn_frame = tk.Frame(dialog, bg="#0a0a0a")
    btn_frame.pack(side="bottom", pady=20)

    # Кнопка отказа
    btn_exit = tk.Button(
        btn_frame, 
        text="Я не хочу продолжать, спасибо", 
        command=on_stop,
        bg="#1a1a1a",
        fg="#ff4444",
        font=("Consolas", 9, "bold"),
        activebackground="#333",
        activeforeground="#ff0000",
        relief="flat",
        padx=10
    )
    btn_exit.pack(side="left", padx=10)

    # Кнопка согласия
    btn_proceed = tk.Button(
        btn_frame, 
        text="Мне стало лишь интереснее", 
        command=on_continue,
        bg="#1a1a1a",
        fg="#00ff00",
        font=("Consolas", 9, "bold"),
        activebackground="#333",
        activeforeground="#00ff00",
        relief="flat",
        padx=10
    )
    btn_proceed.pack(side="left", padx=10)

    # Запрещаем закрывать окно крестиком (только через кнопки)
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    root.mainloop()