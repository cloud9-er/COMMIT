import urllib.request
from urllib.parse import urlsplit
import http.client
import urllib.error

import ssl

url = "https://books.toscrape.com"

class URL():
    def __init__(self, scheme, netloc, path = None, query = None, fragment = None):
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        self.query = query
        self.fragment = fragment

class ConnectionKey():
    def __init__(self, host, port):
        self.host = host
        self.port = port

class HTTPConnectionManager():
    def __init__(self, maximum = 2, timeout = 5.0):
        self.maximum = maximum
        self.timeout = timeout

        self._ssl_context = ssl.create_default_context()

    def create(self, key):
        return http.client.HTTPSConnection(host = key.host, key = key.port, timeout = self.timeout, context = self._ssl_context)

    def acquire(self, host, port = 443):
        pass
    def release(self, conn):
        pass

    def shutdown(self, conn):
        pass

def decompose(url):
    decomposed = urlsplit(url)
    decomposed_dict = {
        "scheme" : decomposed.scheme,
        "host" : decomposed.netloc,
        "path" : decomposed.path,
        "query" : decomposed.query,
        "fragment" : decomposed.fragment
    }
    return decomposed_dict

def connect(host, port = 443):
    return http.client.HTTPSConnection(host, port)

def get_response(url):
    try:
        with urllib.request.urlopen(url) as response:
            headers = response.getheaders()
            content = response.read().decode("utf-8")

    except urllib.error.HTTPError as e:
        print(e.status)

    finally:
        #location for ConnectionManager
        conn.close()
        return content

decomposed = decompose(url)
conn = connect(decomposed["host"])
response = get_response(url)

