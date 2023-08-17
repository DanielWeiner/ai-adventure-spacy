from dotenv import load_dotenv
from threading import Thread
from src.main import handler as main_handler, load_nlp

load_dotenv()

nlp_thread = Thread(target=load_nlp)
nlp_thread.start()

def handler(event, context):
    return main_handler(event, context)