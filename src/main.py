from typing import Optional
from spacy import Language, load as spacy_load
import src.spacy_parser as spacy_parser
from threading import Lock, Event
import importlib
import os
import json

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
    
def handler(event, context):
    assert isinstance(event, dict)
    
    is_request = "requestContext" in event
    text = event.get("body", "") if is_request else event.get("text", "")

    if is_request and event["requestContext"]["http"]["method"] != "POST":
        return {
            "statusCode": 404,
            "body": "Not Found"
        }

    nlp, nlp_coref = get_nlp()
    if (is_dev_environment() == "dev"):
        importlib.reload(spacy_parser)

    resp = spacy_parser.parse(nlp, nlp_coref, text)

    if is_request:
        resp = {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(resp)
        }
    return resp
