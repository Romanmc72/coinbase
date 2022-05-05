#!/usr/bin/env python3
"""Unit tests for the authenticator module"""
import hashlib
import hmac
import unittest
from unittest.mock import patch

from cb.auth import authenticator
from cb.auth.authenticator import CoinbaseAuth

FAKE_API_KEY = "This ain't no API key..."
FAKE_SECRET_KEY = "I have no secrets, I am an open book..."


class TestAuthenticator(unittest.TestCase):
    @patch.dict(
        "os.environ", {"CB_API_KEY": FAKE_API_KEY, "CB_SECRET_KEY": FAKE_SECRET_KEY}
    )
    def test_authenticate_from_env(self):
        coinbase_auth = authenticator.CoinbaseAuth()
        self.assertEqual(coinbase_auth.api_key, FAKE_API_KEY)
        self.assertEqual(coinbase_auth.secret_key, FAKE_SECRET_KEY)

    def test_authenticate_passed_in(self):
        coinbase_auth = authenticator.CoinbaseAuth(
            api_key=FAKE_API_KEY,
            secret_key=FAKE_SECRET_KEY,
        )
        self.assertEqual(coinbase_auth.api_key, FAKE_API_KEY)
        self.assertEqual(coinbase_auth.secret_key, FAKE_SECRET_KEY)

    @patch("cb.auth.authenticator.os")
    def test_authenticate_raises(self, mock_os):
        mock_os.getenv.return_value = None
        self.assertRaises(
            authenticator.CoinbaseAuthException,
            authenticator.CoinbaseAuth,
            **{"api_key": None, "secret_key": None},
        )

    @patch("cb.auth.authenticator.datetime")
    @patch("cb.auth.authenticator.time")
    @patch("cb.auth.authenticator.requests")
    def test_requests__call__headers(self, mock_requests, mock_time, mock_datetime):
        fake_timestamp = "1234567890"
        fake_date = "1999-01-01"
        fake_method = "GET"
        fake_path_url = "https://fancy-api/"

        mock_requests.method = fake_method
        mock_requests.path_url = fake_path_url
        mock_requests.body = None
        mock_requests.headers = {}
        mock_time.time.return_value = fake_timestamp
        mock_datetime.return_value.date.return_value = fake_date

        fake_auth = CoinbaseAuth(api_key=FAKE_API_KEY, secret_key=FAKE_SECRET_KEY)
        fake_auth.__call__(request=mock_requests)
        self.assertEqual(
            mock_requests.headers,
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "CB-ACCESS-KEY": FAKE_API_KEY,
                "CB-ACCESS-SIGN": hmac.new(
                    key=FAKE_SECRET_KEY.encode("utf8"),
                    msg=(fake_timestamp + fake_method + fake_path_url + "").encode(
                        "utf8"
                    ),
                    digestmod=hashlib.sha256,
                ).hexdigest(),
                "CB-ACCESS-TIMESTAMP": fake_timestamp,
                "CB-VERSION": fake_date,
            },
        )


if __name__ == "__main__":
    unittest.main()
