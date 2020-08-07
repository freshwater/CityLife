
import http.server

import json
import psycopg2

class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        index_file = file.read()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        request = json.loads(data)

        print("Request")
        print(json.dumps(request).encode()[:800])

        response = {
            'AllCorrect': 'True',
            'Response': {}
        }

        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        response = Server.index_file

        self.wfile.write(response.encode())


def database_initialize():
    cursor = connection.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS pages (key varchar PRIMARY KEY, value varchar);
        CREATE TABLE IF NOT EXISTS pages_metadata (key varchar PRIMARY KEY, value jsonb);

        COMMIT;

    """)
    
        
def run(port=80):
    global connection

    connection_string = "host='postgres' port='5432' dbname='postgres' user='postgres' password='password'"

    print(f'Connecting to database\n -> {connection_string}')
    connection = psycopg2.connect(connection_string)

    database_initialize()

    print("Listening on port", str(port) + ".")

    httpd = http.server.HTTPServer(('', port), Server)
    httpd.serve_forever()


run()
