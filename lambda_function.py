from src.main import handler as main_handler

def handler(event, context):
    return main_handler(event, context)