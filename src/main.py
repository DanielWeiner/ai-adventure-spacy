from typing import Optional
from spacy import Language, load as spacy_load
import src.spacy_parser as spacy_parser
from threading import Lock, Event
import importlib
import os
import json

SPACY_LATEST_VERSION_FILE = os.getenv("SPACY_LATEST_VERSION_FILE", "/dev/null")

request_headers = {
    "Content-Type": "application/json; charset=utf-8"
}

class NlpState:
    def __init__(self) -> None:
        self.nlp : Optional[Language] = None
        self.nlp_coref : Optional[Language] = None
        self.lock = Lock()
        self.event = Event()

nlp_state = NlpState()

def is_dev_environment():
    return os.getenv("SPACY_SERVER_ENV", "prod") == "dev"

def load_nlp():
    print("Loading language models.")

    nlp = spacy_load("en_core_web_trf")
    nlp_coref = spacy_load("en_coreference_web_trf", vocab=nlp.vocab)

    print("Language models loaded.")

    with nlp_state.lock:
        nlp_state.nlp = nlp
        nlp_state.nlp_coref = nlp_coref
        nlp_state.event.set()

def get_nlp():
    nlp_state.event.wait()
    with nlp_state.lock:
        nlp : Language = nlp_state.nlp
        nlp_coref : Language = nlp_state.nlp_coref
        return nlp, nlp_coref
    
def http_response(status: int, content):
    return {
        "statusCode": status,
        "headers":    request_headers,
        "body":       json.dumps(content)
    }

def handler(event, context):
    assert isinstance(event, dict)

    is_request = "requestContext" in event
    text = event.get("body", "") if is_request else event.get("text", "")

    if is_request and event["requestContext"]["http"]["method"] != "POST":
        return {
            "statusCode": 404,
            "headers": request_headers,
            "body": json.dumps("Not Found")
        }
    
    if event.get("warmup") == True:
        if event.get("new_version") is not None:
            with open(SPACY_LATEST_VERSION_FILE, "w") as file:
                print(f"Writing {event['new_version']} to {SPACY_LATEST_VERSION_FILE}")
                file.write(str(event["new_version"]))

        nlp, nlp_coref = get_nlp()
        nlp_coref(nlp(""))

        if is_request:
            return {
                "statusCode": 200,
                "body": json.dumps("OK")
            }
        else:
            return "OK"
        
    if (is_dev_environment() == "dev"):
        importlib.reload(spacy_parser)

    resp = spacy_parser.parse(get_nlp, text)

    return http_response(201, resp) if is_request else resp
