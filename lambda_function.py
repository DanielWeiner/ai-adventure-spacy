from dotenv import load_dotenv
from threading import Thread
from src.main import handler as main_handler, load_nlp, is_dev_environment
import boto3
import json
import signal
import os

load_dotenv()

nlp_thread = Thread(target=load_nlp)
nlp_thread.start()

def self_invoke():
    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName=os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
        InvocationType="Event",
        Payload=bytes(json.dumps({
            "text": ""
        }))
    )

def handle_shutdown(*_):
    if not is_dev_environment():
        self_invoke()

signal.signal(signal.SIGTERM, handle_shutdown)

def handler(event, context):
    return main_handler(event, context)