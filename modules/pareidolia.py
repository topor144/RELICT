import random
from pareidolia_engine import PareidoliaFilter # Предполагаем наличие фильтра в папке или внутри

def execute(core, decision, user_input):
    # Адаптация: используем векторы из decision
    v = decision["state"]["vectors"]
    corruption = v.get("corruption", 0)
    panic = v.get("panic", 0)

    # Если Артем нестабилен, он "загрязняет" буфер обмена или логи
    if corruption > 0.6 or panic > 0.7:
        # Логика: Артем пытается исказить то, что видит пользователь
        # В данном случае модуль может влиять на стиль вывода (style)
        if decision["style"] == "GLITCH":
            # Дополнительная обработка не требуется, 
            # так как ядро само применяет стиль к ответу.
            pass