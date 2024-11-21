import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class CalculatorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        operation = query.get('operation', [None])[0]
        num1 = float(query.get('num1', [0])[0])
        num2 = float(query.get('num2', [0])[0])

        if operation and num1 is not None and num2 is not None:
            result = calculator(operation, num1, num2)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(result).encode())
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Error: Invalid parameters')

def run(server_class=HTTPServer, handler_class=CalculatorHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()