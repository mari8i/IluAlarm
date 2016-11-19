from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
import json
import re

class JSONRequestHandler (BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
        return

    def find_url(self):
        for u in self.urls:
            _match = u[1].match(self.path)
            if _match:
                # Match, get, post, delete
                return (_match, u[2], u[3], u[4])
        return None
    
    def do_GET(self):
        try:
            methods = self.find_url()

            # First of all, handle errors..
            if methods is None or methods[1] is None:
                self.send_response(404)
                return

            do_stuff = methods[1](self.path, methods[0], self.bundle)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Client', str(self.client_address))
            self.send_header('User-agent', str(self.headers['user-agent']))
            self.send_header('Path', self.path)
            self.end_headers()

            self.wfile.write(json.dumps(do_stuff))
        except Exception as e:
            print e
            self.send_response(500)

        return
    

    def do_POST(self):
        try:
            methods = self.find_url()

            # First of all, handle errors..
            if methods is None or methods[2] is None:
                self.send_response(404)
                return

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'application/json':
                length = int(self.headers.getheader('content-length'))
                json_str = self.rfile.read(length)
                json_data = json.loads(json_str)
            else:
                print e
                self.send_response(500)
                return

            do_stuff = methods[2](self.path, methods[0], json_data, self.bundle)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Client', str(self.client_address))
            self.send_header('User-agent', str(self.headers['user-agent']))
            self.send_header('Path', self.path)
            self.end_headers()

            self.wfile.write(json.dumps(do_stuff))
        except Exception as e:
            print e
            self.send_response(500)

            
    def do_DELETE(self):
        try:
            methods = self.find_url()

            # First of all, handle errors..
            if methods is None or methods[3] is None:
                self.send_response(404)
                return

            do_stuff = methods[3](self.path, methods[0], self.bundle)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Client', str(self.client_address))
            self.send_header('User-agent', str(self.headers['user-agent']))
            self.send_header('Path', self.path)
            self.end_headers()

            self.wfile.write(json.dumps(do_stuff))
        except Exception as e:
            print e
            self.send_response(500)

        return
    
def make_request_handler(urls, bundle):
    class TmpHandler(JSONRequestHandler):
        def __init__(self, *args, **kwargs):
            self.urls = urls
            self.bundle = bundle
            JSONRequestHandler.__init__(self, *args, **kwargs)
    return TmpHandler


class JSONServer(object):


    def __init__(self, host, port, bundle=None):
        self.server_params = (host, port)
        self.server = None
        self.urls = []
        self.bundle = bundle
        return

    def register_url(self, regex, get=None, post=None, delete=None):
        self.urls.append((regex, re.compile(regex), get, post, delete))

    def serve_forever(self):
        if self.server is None:
            self.server = HTTPServer(self.server_params,
                                     make_request_handler(self.urls, self.bundle))

        self.server.serve_forever()

    pass
