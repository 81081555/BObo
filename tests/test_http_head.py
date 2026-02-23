import http.client
import threading
import time
import unittest
from http.server import ThreadingHTTPServer

from app import AppHandler


class HttpHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), AppHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def test_head_root_returns_200(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request("HEAD", "/")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.read(), b"")
        conn.close()

    def test_head_health_returns_200(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request("HEAD", "/api/health")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.read(), b"")
        conn.close()


if __name__ == '__main__':
    unittest.main()
