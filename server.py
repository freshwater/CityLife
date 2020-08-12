
import http.server

import json
import time
import psycopg2

class Server(http.server.BaseHTTPRequestHandler):
    with open('index.html') as file:
        html_index_file = file.read()

    with open('/database/coordinates_word_index.json', 'r') as file:
        t0 = time.time()
        coordinates_word_index = {key: set(value) for key, value in json.loads(file.read()).items()}
        print(f'Coordinates index load time: {time.time() - t0:.1f}')

    with open('/database/titles_word_index.json', 'r') as file:
        t0 = time.time()
        titles_word_index = {key: set(value) for key, value in json.loads(file.read()).items()}
        print(f'Titles index load time: {time.time() - t0:.1f}')

    with open('/database/coordinates_list.json', 'r') as file:
        t0 = time.time()
        coordinates_list = json.loads(file.read())
        print(f'Coordinates load time: {time.time() - t0:.1f}')

    with open('/database/article_titles_array.json', 'r') as file:
        t0 = time.time()
        article_titles_list = json.loads(file.read())
        print(f'Titles load time: {time.time() - t0:.1f}')

    with open('/database/coordinates_articles_index_array.json', 'r') as file:
        t0 = time.time()
        coordinates_articles_index = json.loads(file.read())
        print(f'Coordinate-Articles index load time: {time.time() - t0:.1f}')

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

        import functools
        coordinate_index_sets = [Server.coordinates_word_index.get(word, set()) for word in query_text.split()] or [set()]
        coordinate_indices = functools.reduce(set.intersection, coordinate_index_sets)
        # coordinates = [Server.coordinates_list[index] for index in coordinate_indices]

        title_index_sets = [Server.titles_word_index.get(word, set()) for word in query_text.split()] or [set()]
        title_indices = functools.reduce(set.intersection, title_index_sets)
        # titles = [Server.article_titles_list[index] for index in title_indices]

        # each coordinate can have multiple associated articles
        coordinate_title_pairs = []
        for coordinate_index in coordinate_indices:
            coordinate = Server.coordinates_list[coordinate_index]
            article_indices = Server.coordinates_articles_index[coordinate_index]

            # attach to coordinate only those titles whose articles match search criteria
            article_indices = [index for index in article_indices if index in title_indices]
            article_titles = [Server.article_titles_list[index] for index in article_indices]

            coordinate_title_pairs.append((coordinate, article_titles))

        response = {
            'AllCorrect': 'True',
            'Response': {
                # 'Coordinates': coordinates,
                # 'ArticleTitles': titles,
                'CoordinateTitlePairs': coordinate_title_pairs
            }
        }

        print(f'QueryTime: {time.time() - t0}')

        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        response = Server.html_index_file

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
