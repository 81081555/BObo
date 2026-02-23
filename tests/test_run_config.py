import os
import unittest
from unittest.mock import patch

import app


class RunConfigTests(unittest.TestCase):
    def test_run_uses_host_port_from_environment(self) -> None:
        with patch.dict(os.environ, {"HOST": "127.0.0.1", "PORT": "18000"}, clear=False):
            with patch("app.ThreadingHTTPServer") as mock_server:
                app.run()

        mock_server.assert_called_once_with(("127.0.0.1", 18000), app.AppHandler)
        mock_server.return_value.serve_forever.assert_called_once()


if __name__ == "__main__":
    unittest.main()
