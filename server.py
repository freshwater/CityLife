
import http.server

import json
import time
import psycopg2

class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        index_file = file.read()

    with open('/database/coordinates_master_list.json', 'r') as file:
        t0 = time.time()
        coordinates_master_list = json.loads(file.read())
        print(f'Coordinates load time: {time.time() - t0:.1f}')

    with open('/database/master_index.json', 'r') as file:
        t0 = time.time()
        master_index = {key: set(value) for key, value in json.loads(file.read()).items()}
        print(f'Index load time: {time.time() - t0:.1f}')

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        request = json.loads(data)

        print("Request")
        print(json.dumps(request).encode()[:800])

        query_text = request['QueryText']
        
        t0 = time.time()

        coordinate_index_sets = [Server.master_index.get(word, set()) for word in query_text.split()]
        # print(sum(map(len, coordinate_index_sets)))

        import functools
        coordinate_indices = functools.reduce(set.intersection, coordinate_index_sets)
        # print(len(coordinate_indices))

        coordinates = [Server.coordinates_master_list[index] for index in coordinate_indices]

        response = {
            'AllCorrect': 'True',
            'Response': {
                'Coordinates': coordinates
            }
        }

        print(f'QueryTime: {time.time() - t0}')

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
