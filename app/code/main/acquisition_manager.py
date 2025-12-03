from threading import Thread
from main.acquisition_adapter import CSV_adapter
from flask import current_app

adapter_instance = None
thread_instance = None

def start():
    global adapter_instance, thread_instance
    if adapter_instance is None:
        adapter_instance = CSV_adapter()
        app = current_app._get_current_object()
        thread_instance = Thread(target=adapter_instance.data_polling, args=(app,), daemon=True)
        thread_instance.start()
        return True
    return False

def stop():
    global adapter_instance
    if adapter_instance is not None:
        adapter_instance.stop()
        adapter_instance = None
        return True
    return False