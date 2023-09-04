from concurrent.futures import ThreadPoolExecutor
from spacy import load as spacy_load
import src.spacy_parser as spacy_parser
import os
import json
import amrlib

SPACY_LATEST_VERSION_FILE = os.getenv("SPACY_LATEST_VERSION_FILE", "/dev/null")

request_headers = {
    "Content-Type": "application/json; charset=utf-8"
}

def load_base_nlp():
    print("Loading base language model.")

    nlp = spacy_load("en_core_web_trf")

    print("Base language model loaded.")
    
    return nlp

def load_coref_nlp():
    print("Loading coreference model.")

    nlp_coref = spacy_load("en_coreference_web_trf")
    nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
    nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])

    print("Coreference model loaded.")

    return nlp_coref

def load_amr():
    print("Loading AMR.")
    
    amrlib.load_stog_model("amrlib/data/model_stog", device="cpu")
    amrlib.setup_spacy_extension()

    print("AMR Loaded.")

def load_nlp():
    with ThreadPoolExecutor(max_workers=3) as executor:
        base_nlp_future = executor.submit(load_base_nlp)
        coref_nlp_future = executor.submit(load_coref_nlp)
        amr_future = executor.submit(load_amr)

    nlp = base_nlp_future.result()
    nlp_coref = coref_nlp_future.result()
    amr_future.result()

    print("All models loaded.")

    nlp.add_pipe("coref", source=nlp_coref)
    nlp.add_pipe("span_resolver", source=nlp_coref)
    nlp.add_pipe("span_cleaner", source=nlp_coref)

    return nlp

def http_response(status: int, content):
    return {
        "statusCode": status,
        "headers":    request_headers,
        "body":       json.dumps(content)
    }

executor = ThreadPoolExecutor(max_workers=1)
nlp_future = executor.submit(load_nlp)
executor.shutdown(wait=False)

def handler(event, context):
    assert isinstance(event, dict)

    print(f"User home: {os.path.expanduser('~')}")
    print(f"Transformers cache: {os.getenv('TRANSFORMERS_CACHE', '')}")
    print("Transformers cache files:")
    for dir in os.listdir(os.getenv('TRANSFORMERS_CACHE', '')):
        print(dir)

    is_request = "requestContext" in event
    text = event.get("body", "") if is_request else event.get("text", "")

    if is_request and event["requestContext"]["http"]["method"] != "POST":
        return http_response(404, "Not Found")
    
    if event.get("warmup") == True:
        if event.get("new_version") is not None:
            with open(SPACY_LATEST_VERSION_FILE, "w") as file:
                print(f"Writing {event['new_version']} to {SPACY_LATEST_VERSION_FILE}")
                file.write(str(event["new_version"]))

        nlp = nlp_future.result()
        nlp(" ")
        return ""
    
    resp = spacy_parser.parse(nlp_future, text)
    return http_response(201, resp) if is_request else resp
