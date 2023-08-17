#!/usr/bin/env python3

import boto3
import os
import json
import signal

lambda_client = boto3.client("lambda")

def handle_signal(*_):
    print('Received SIGTERM. Shutting down.')
    lambda_client.invoke(
        FunctionName=os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
        InvocationType="Event",
        Payload=bytes(json.dumps({
            "text": ""
        }))
    )


def main():
    print("Adding self-invoke on shutdown functionality.")
    signal.signal(signal.SIGTERM, handle_signal)

if __name__ == "__main__":
    main()