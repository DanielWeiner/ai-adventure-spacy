import spacy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import spacy_parser
import signal
import requests
from google.cloud import run_v2
import threading
from time import sleep
import importlib

load_dotenv()

SPACY_SERVER_HOST = os.getenv("SPACY_SERVER_HOST", "0.0.0.0")
SPACY_SERVER_PORT = int(os.getenv("SPACY_SERVER_PORT", "80"))
SPACY_SERVER_ENV = os.getenv("SPACY_SERVER_ENV", "dev")
SERVICE_NAME = os.getenv("K_SERVICE", "")

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
}

nlp_lock = threading.Lock()
shared_state : dict[str, spacy.Language] = {}

def load_nlp(shared_state: dict[str, spacy.Language]):
    print("Loading language models.")

    nlp = spacy.load("en_core_web_trf")
    nlp_coref = spacy.load("en_coreference_web_trf", vocab=nlp.vocab)

    print("Language models loaded.")

    with nlp_lock:
        shared_state["nlp"] = nlp
        shared_state["nlp_coref"] = nlp_coref

def get_nlp():
    while True:
        with nlp_lock:
            if "nlp" in shared_state and "nlp_coref" in shared_state:
                return shared_state["nlp"], shared_state["nlp_coref"]
        sleep(0.01)

class SpacyRequestHandler(BaseHTTPRequestHandler):        
    def send_headers(self) -> None:
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()

    def do_GET(self):
        response_code = 200
        response_body = ""

        parsed_url = urlparse(self.path)
        if parsed_url.path == "/health":
            response_code = 200
        else:
            response_code = 404

        self.send_response(response_code)
        self.send_headers()

        if parsed_url.path == "/health":
            response_body = "OK"
        else:
            response_body = "Not Found"
        
        self.wfile.write(bytes(response_body, "utf-8"))

    def do_POST(self):
        response_code = 200
        response_body = ""
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/parse":
            response_code = 200
        else:
            response_code = 404
        
        self.send_response(response_code)
        self.send_headers()

        if self.path == "/parse":
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len).decode("utf-8")
            response_body = ""
            
            if post_body is None:
                response_body = "null"
            else:
                nlp, nlp_coref = get_nlp()
                if (SPACY_SERVER_ENV == "dev"):
                    importlib.reload(spacy_parser)
                response_body = spacy_parser.parse(nlp, nlp_coref, post_body)
        else:
            response_body = "Not Found"
        
        self.wfile.write(bytes(response_body, "utf-8"))

def get_instance_metadata():
    url = "http://metadata.google.internal/computeMetadata/v1/instance/region"
    headers={
        "Metadata-Flavor": "Google"
    }
    resp = requests.get(url, headers=headers)
    instance_info = resp.text
    parts = instance_info.split("/")
    project_number = parts[1]
    region = parts[3]
    return project_number, region

def get_service_url():
    project_number, region = get_instance_metadata()
    url = f'projects/{project_number}/locations/{region}/services/{SERVICE_NAME}'
    client = run_v2.ServicesClient()
    request = run_v2.GetServiceRequest(name=url)
    response = client.get_service(request=request)
    service_url = response.uri
    return service_url

def invoke_service():
    service_url = get_service_url()
    requests.get(f'{service_url}/health')
        
if __name__ == "__main__":
    nlp_thread = threading.Thread(target=load_nlp, args=(shared_state,))
    nlp_thread.start()

    webServer = ThreadingHTTPServer((SPACY_SERVER_HOST, SPACY_SERVER_PORT), SpacyRequestHandler)
    print("Server started %s:%s." % (SPACY_SERVER_HOST, SPACY_SERVER_PORT))

    def stop_server(*_):
        nlp_thread.join()
        webServer.server_close()
        print("Server stopped.")
        if (SPACY_SERVER_ENV == "prod"):
            print("Handling SIGTERM: restarting service.")
            invoke_service()
        
    signal.signal(signal.SIGTERM, stop_server)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        stop_server()
