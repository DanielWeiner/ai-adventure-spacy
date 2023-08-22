#!/usr/bin/env python3

import os
import json
import requests
import sys
from pathlib import Path

LAMBDA_EXTENSION_NAME =     Path(__file__).parent.name
LAMBDA_FUNCTION_NAME =      os.getenv("AWS_LAMBDA_FUNCTION_NAME")
LAMBDA_FUNCTION_VERSION =   os.getenv("AWS_LAMBDA_FUNCTION_VERSION")
LAMBDA_RUNTIME_API =        os.getenv("AWS_LAMBDA_RUNTIME_API")
SPACY_LATEST_VERSION_FILE = os.getenv("SPACY_LATEST_VERSION_FILE", "/dev/null")
BASE_RUNTIME_API_URL =      f"http://{LAMBDA_RUNTIME_API}/2020-01-01/extension"
REGISTER_URL =              f"{BASE_RUNTIME_API_URL}/register"
NEXT_EVENT_URL =            f"{BASE_RUNTIME_API_URL}/event/next"

def log(output: str):
    print(json.dumps({
        "extension": LAMBDA_EXTENSION_NAME,
        "function":  LAMBDA_FUNCTION_NAME,
        "version":   LAMBDA_FUNCTION_VERSION,
        "content":   output
    }), flush=True)

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
        if not os.path.exists(SPACY_LATEST_VERSION_FILE):
            log(f"File not found: {SPACY_LATEST_VERSION_FILE}")
            return
        with open(SPACY_LATEST_VERSION_FILE, "r") as file:
            latest_version = file.read().strip()
            if (LAMBDA_FUNCTION_VERSION != latest_version):
                log(f"Version mismatch: {latest_version}")
                return
        log("self-invoke")

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
