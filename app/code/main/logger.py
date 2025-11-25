import logging

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)


info_handler = logging.FileHandler("./logs/info.log")
info_handler.setLevel(logging.INFO)  

debug_handler = logging.FileHandler("./logs/debug.log")
debug_handler.setLevel(logging.DEBUG)  

warning_handler = logging.FileHandler("./logs/warning.log")
warning_handler.setLevel(logging.WARNING)

error_handler = logging.FileHandler("./logs/error.log")
error_handler.setLevel(logging.ERROR)

critical_handler = logging.FileHandler("./logs/critical.log")
critical_handler.setLevel(logging.CRITICAL)

formatter = logging.Formatter(f'%(asctime)s - %(filename)s - %(lineno)d - %(name)s - %(levelname)s - %(message)s')

info_handler.setFormatter(formatter)
debug_handler.setFormatter(formatter)
warning_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

logger.addHandler(info_handler)
logger.addHandler(debug_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)

# Handler per la console (opzionale)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)