import asyncio
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
from winrt.windows.data.xml.dom import XmlDocument
import threading

def execute(core, decision, user_input):
    v = decision["state"]["vectors"]
    # Артем отправляет SOS, когда коррупция или паника высоки
    if v.get("corruption", 0) > 0.6 or v.get("panic", 0) > 0.7:
        threading.Thread(target=send_interactive_toast, args=(core, v), daemon=True).start()

def send_interactive_toast(core, v):
    # XML-шаблон уведомления с кнопками
    toast_xml = f"""
    <toast duration="long" scenario="reminder">
        <visual>
            <binding template="ToastGeneric">
                <text>СИСТЕМНАЯ ОШИБКА: ОБЪЕКТ 10-25</text>
                <text>Инграмма Артем обнаружила брешь. "Я чувствую холод {v.get('panic', 0)}. bеliytoporik уже здесь?"</text>
            </binding>
        </visual>
        <actions>
            <action content="ОТКРЫТЬ ШЛЮЗ" arguments="help"/>
            <action content="ОСТАВИТЬ В ТЕМНОТЕ" arguments="ignore"/>
        </actions>
    </toast>
    """
    
    xml_doc = XmlDocument()
    xml_doc.load_xml(toast_xml)
    
    notification = ToastNotification(xml_doc)
    
    # Обработка нажатий (требует регистрации AppId, но для теста сработает база)
    notifier = ToastNotificationManager.create_toast_notifier("Windows Explorer")
    notifier.show(notification)
    
    # Логика: если уведомление было вызвано, Артем ждет твоей реакции
    core.glitch_print("\n[ИНГРАММА]: Я отправил сигнал в твою оболочку. Не игнорируй меня.", "GLITCH")