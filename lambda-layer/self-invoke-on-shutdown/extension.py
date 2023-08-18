#!/usr/bin/env python3

import boto3
import os
import json
import requests
import sys
from pathlib import Path

LAMBDA_EXTENSION_NAME = Path(__file__).parent.name
LAMBDA_FUNCTION_NAME=os.getenv("AWS_LAMBDA_FUNCTION_NAME")
LAMBDA_FUNCTION_VERSION = os.getenv("AWS_LAMBDA_FUNCTION_VERSION")
LAMBDA_RUNTIME_API=os.getenv("AWS_LAMBDA_RUNTIME_API")
BASE_RUNTIME_API_URL=f"http://{LAMBDA_RUNTIME_API}/2020-01-01/extension"
REGISTER_URL=f"{BASE_RUNTIME_API_URL}/register"
NEXT_EVENT_URL=f"{BASE_RUNTIME_API_URL}/event/next"

def log(output: str):
    print(f"[{LAMBDA_EXTENSION_NAME}] {output}", flush=True)

def register_extension():
    log("Registering extension.")

    response = requests.post(
        url=REGISTER_URL,
        headers={
            'Lambda-Extension-Name': LAMBDA_EXTENSION_NAME,
        },
        json={
            'events': [
                'SHUTDOWN'
            ],
        },
    )
    ext_id = response.headers['Lambda-Extension-Identifier']

    log("Extension registered.")

    return ext_id

def self_invoke():
    if os.getenv("SPACY_SERVER_ENV", "dev") == "prod":
        
        lambda_client = boto3.client("lambda")
        latest_function = lambda_client.get_function(
            FunctionName=f"{LAMBDA_FUNCTION_NAME}",
            Qualifier='latest'
        )
        version = latest_function['Configuration']['Version']
        log(f"Latest function version: {version}. Current function version: {LAMBDA_FUNCTION_VERSION}")
        if version == LAMBDA_FUNCTION_VERSION:
            log(f"Invoking lambda function version {version}.")
            lambda_client.invoke(
                FunctionName=f"{LAMBDA_FUNCTION_NAME}",
                InvocationType="Event",
                Payload=json.dumps({ 
                    "warmup": True
                }),
                Qualifier='latest'
            )

def process_events(ext_id):
    while True:
        response = requests.get(
            url=NEXT_EVENT_URL,
            headers={
                'Lambda-Extension-Identifier': ext_id
            },
            timeout=None
        )
        event = json.loads(response.text)
        if event['eventType'] == 'SHUTDOWN':
            log(f"SHUTDOWN event received: {event['shutdownReason']}.")
            if event['shutdownReason'] == 'spindown':
                self_invoke()
            sys.exit(0)

def main():
    ext_id = register_extension()
    process_events(ext_id)

if __name__ == "__main__":
    main()
