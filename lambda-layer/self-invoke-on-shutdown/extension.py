#!/usr/bin/env python3

import boto3
import os
import json
import requests
import sys
from pathlib import Path

LAMBDA_EXTENSION_NAME = Path(__file__).parent.name

def register_extension():
    print(f"[{LAMBDA_EXTENSION_NAME}] Registering extension.", flush=True)
    headers = {
        'Lambda-Extension-Name': LAMBDA_EXTENSION_NAME,
    }
    payload = {
        'events': [
            'SHUTDOWN'
        ],
    }
    response = requests.post(
        url=f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/register",
        json=payload,
        headers=headers
    )
    ext_id = response.headers['Lambda-Extension-Identifier']
    
    print(f"[{LAMBDA_EXTENSION_NAME}] Extension registered.", flush=True)

    return ext_id

def self_invoke():
    if os.getenv("SPACY_SERVER_ENV", "dev") == "prod":
        print(f"[{LAMBDA_EXTENSION_NAME}] Invoking lambda function.", flush=True)
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName=os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            InvocationType="Event",
            Payload=bytes(json.dumps({
                "text": ""
            }))
        )

def process_events(ext_id):
    headers = {
        'Lambda-Extension-Identifier': ext_id
    }
    while True:
        response = requests.get(
            url=f"http://{os.environ['AWS_LAMBDA_RUNTIME_API']}/2020-01-01/extension/event/next",
            headers=headers,
            timeout=None
        )
        event = json.loads(response.text)
        if event['eventType'] == 'SHUTDOWN':
            print(f"[{LAMBDA_EXTENSION_NAME}] SHUTDOWN event received: {event['shutdownReason']}.", flush=True)
            if event['shutdownReason'] == 'SPINDOWN':
                self_invoke()
            sys.exit(0)

def main():
    ext_id = register_extension()
    process_events(ext_id)

if __name__ == "__main__":
    main()
