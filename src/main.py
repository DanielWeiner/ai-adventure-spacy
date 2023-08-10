import spacy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from spacy_parser import parse
import signal

load_dotenv()

SPACY_SERVER_HOST = os.getenv("SPACY_SERVER_HOST", "0.0.0.0")
SPACY_SERVER_PORT = int(os.getenv("SPACY_SERVER_PORT", "80"))

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
}

class SpacyServer(ThreadingHTTPServer):
    def __init__(self, server_address, bind_and_activate: bool = True) -> None:
        print("Initializing spaCy")
        self.nlp  = spacy.load("en_core_web_trf")
        super().__init__(server_address, SpacyRequestHandler, bind_and_activate)
        
    def get_nlp(self) -> spacy.Language:
        return self.nlp

class SpacyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server: SpacyServer) -> None:
        self.nlp = server.get_nlp()
        super().__init__(request, client_address, server)
        
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
                response_body = parse(self.nlp, post_body)
        else:
            response_body = "Not Found"
        
        self.wfile.write(bytes(response_body, "utf-8"))
        
if __name__ == "__main__":
    webServer = SpacyServer((SPACY_SERVER_HOST, SPACY_SERVER_PORT))
    print("Server started http://%s:%s" % (SPACY_SERVER_HOST, SPACY_SERVER_PORT))

    def stop_server(a=None,b=None):
        print("Server stopped.")
        webServer.server_close()

    signal.signal(signal.SIGTERM, stop_server)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        stop_server()
