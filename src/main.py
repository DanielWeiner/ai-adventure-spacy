from typing import Optional
from spacy import Language, load as spacy_load
import src.spacy_parser as spacy_parser
from threading import Lock, Event, Thread
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

def load_base_nlp():
    print("Loading base language model.")

    nlp = spacy_load("en_core_web_trf")

    with nlp_state.lock:
        nlp_state.nlp = nlp

def load_coref_nlp():
    print("Loading coreference model.")

    nlp_coref = spacy_load("en_coreference_web_trf")

    nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
    nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])

    with nlp_state.lock:
        nlp_state.nlp_coref = nlp_coref

def load_nlp():
    print("Loading language models.")

    base_thread = Thread(target=load_base_nlp)
    coref_thread = Thread(target=load_coref_nlp)

    base_thread.start()
    coref_thread.start()
    base_thread.join()
    coref_thread.join()

    with nlp_state.lock:
        nlp_state.nlp.add_pipe("coref", source=nlp_state.nlp_coref)
        nlp_state.nlp.add_pipe("span_resolver", source=nlp_state.nlp_coref)
        nlp_state.nlp.add_pipe("span_cleaner", source=nlp_state.nlp_coref)

    print("Language models loaded.")

    with nlp_state.lock:
        nlp_state.nlp_coref = None
        nlp_state.event.set()
        
def get_nlp():
    nlp_state.event.wait()
    with nlp_state.lock:
        nlp : Language = nlp_state.nlp
        return nlp
    
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
        return http_response(404, "Not Found")
    
    if event.get("warmup") == True:
        if event.get("new_version") is not None:
            with open(SPACY_LATEST_VERSION_FILE, "w") as file:
                print(f"Writing {event['new_version']} to {SPACY_LATEST_VERSION_FILE}")
                file.write(str(event["new_version"]))

        nlp = get_nlp()
        nlp("")

        return "OK"

    resp = spacy_parser.parse(get_nlp, text)
    return http_response(201, resp) if is_request else resp
