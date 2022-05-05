#!/usr/bin/env python3
"""Unit tests for the orchestrator module"""
import os
import unittest
from unittest.mock import MagicMock, call, patch

from cb.auth import orchestrator
from cb.auth.authenticator import CoinbaseAuth
from cb.auth.orchestrator import CoinbaseOrchestrator
from cb.currencies import Currency

FAKE_API_URL = "https://butts/"


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.auth = CoinbaseAuth(api_key="Warner", secret_key="Brothers Studios")
        self.orch = CoinbaseOrchestrator(authenticator=self.auth, base_url=FAKE_API_URL)
        self.user = {
            "data": {
                "id": "1234567890987654321",
                "name": "Bugs Bunny",
                "username": "BB1999",
                "profile_location": None,
                "profile_bio": None,
                "profile_url": None,
                "avatar_url": "https://images.coinbase.com/avatar",
                "resource": "user",
                "resource_path": "/v2/user",
                "email": "bugs.bunny@looney.tunes.com",
                "legacy_id": "074t1932phq",
                "time_zone": "Eastern Time (US & Canada)",
                "native_currency": "USD",
                "bitcoin_unit": "BTC",
                "state": "Insanity",
                "country": {
                    "code": "US",
                    "name": "United States of America",
                    "is_in_europe": False,
                },
                "nationality": {"code": "US", "name": "United States of America"},
                "region_supports_fiat_transfers": True,
                "region_supports_crypto_to_crypto_transfers": True,
                "created_at": "1990-01-01T00:00:00Z",
                "supports_rewards": True,
                "tiers": {
                    "completed_description": "Level 3",
                    "upgrade_button_text": None,
                    "header": None,
                    "body": None,
                },
                "referral_money": {
                    "amount": "10.00",
                    "currency": "USD",
                    "currency_symbol": "$",
                    "referral_threshold": "100.00",
                },
                "has_blocking_buy_restrictions": False,
                "has_made_a_purchase": True,
                "has_buy_deposit_payment_methods": True,
                "has_unverified_buy_deposit_payment_methods": False,
                "needs_kyc_remediation": False,
                "show_instant_ach_ux": True,
                "user_type": "individual",
            }
        }

        self.account = {
            "pagination": {
                "ending_before": None,
                "starting_after": None,
                "previous_ending_before": None,
                "next_starting_after": None,
                "limit": 25,
                "order": "desc",
                "previous_uri": None,
                "next_uri": None,
            },
            "data": [
                {
                    "id": "123456789087654321",
                    "name": "DOGE Wallet",
                    "primary": True,
                    "type": "wallet",
                    "currency": {
                        "code": "DOGE",
                        "name": "Dogecoin",
                        "color": "#BA9F33",
                        "sort_index": 129,
                        "exponent": 8,
                        "type": "crypto",
                        "address_regex": "^((D|A|9)[a-km-zA-HJ-NP-Z1-9]{25,34})$",
                        "asset_id": "qwertyuiopasdfghjklzxcvbnm",
                        "slug": "dogecoin",
                    },
                    "balance": {"amount": "100000000.00", "currency": "DOGE"},
                    "created_at": "1990-01-01T00:00:00Z",
                    "updated_at": "1990-01-01T00:00:00Z",
                    "resource": "account",
                    "resource_path": "/v2/accounts/123456789087654321",
                    "allow_deposits": True,
                    "allow_withdrawals": True,
                },
                {
                    "id": "80-9763420982634tupw89",
                    "name": "ETH Wallet",
                    "primary": True,
                    "type": "wallet",
                    "currency": {
                        "code": "ETH",
                        "name": "Ethereum",
                        "color": "#627EEA",
                        "sort_index": 102,
                        "exponent": 8,
                        "type": "crypto",
                        "address_regex": "^(?:0x)?[0-9a-fA-F]{40}$",
                        "asset_id": "80-9763420982634tupw89",
                        "slug": "ethereum",
                    },
                    "balance": {"amount": "60.00", "currency": "ETH"},
                    "created_at": "1990-01-01T00:00:00Z",
                    "updated_at": "1990-01-01T00:00:00Z",
                    "resource": "account",
                    "resource_path": "/v2/accounts/80-9763420982634tupw89",
                    "allow_deposits": True,
                    "allow_withdrawals": True,
                },
                {
                    "id": "279506124837012398751209",
                    "name": "BTC Wallet",
                    "primary": True,
                    "type": "wallet",
                    "currency": {
                        "code": "BTC",
                        "name": "Bitcoin",
                        "color": "#F7931A",
                        "sort_index": 100,
                        "exponent": 8,
                        "type": "crypto",
                        "address_regex": "^([13][a-km-zA-HJ-NP-Z1-9]{25,34})|"
                        + "^(bc1([qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39}|"
                        + "[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{59}))$",
                        "asset_id": "279506124837012398751209",
                        "slug": "bitcoin",
                    },
                    "balance": {"amount": "10.00", "currency": "BTC"},
                    "created_at": "1990-01-01T00:00:00Z",
                    "updated_at": "1990-01-01T00:00:00Z",
                    "resource": "account",
                    "resource_path": "/v2/accounts/279506124837012398751209",
                    "allow_deposits": True,
                    "allow_withdrawals": True,
                },
            ],
        }
        self.exchange_rate = {"data": {"amount": 100000.0}}

    def test_orchestrator_init(self):
        auth = CoinbaseAuth(api_key="Nunya", secret_key="Business")
        orch = orchestrator.CoinbaseOrchestrator(authenticator=auth)
        self.assertEqual(orch.base_url, orchestrator.API_URL)
        self.assertEqual(orch.authenticator, auth)

    @patch("cb.auth.orchestrator.requests")
    def test__post_endpoint(self, mock_request):
        fake_endpoint = "bruh"
        fake_body = {"Sugandeeze": "nutz"}
        mock_response = MagicMock()
        mock_request.post.return_value = mock_response
        self.orch._post_endpoint(endpoint=fake_endpoint, body=fake_body)
        mock_request.post.assert_called_once_with(
            os.path.join(FAKE_API_URL, fake_endpoint), auth=self.auth, body=fake_body
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("cb.auth.orchestrator.requests")
    def test__get_endpoint(self, mock_request):
        fake_endpoint = "dood"
        mock_response = MagicMock()
        mock_request.get.return_value = mock_response
        self.orch._get_endpoint(endpoint=fake_endpoint)
        mock_request.get.assert_called_once_with(
            os.path.join(FAKE_API_URL, fake_endpoint), auth=self.auth
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("cb.auth.orchestrator.requests")
    def test_get_accounts(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = self.account
        mock_request.get.return_value = mock_response
        self.assertEqual(self.orch.get_accounts(), self.account)
        mock_request.get.assert_called_once_with(
            os.path.join(FAKE_API_URL, "accounts"), auth=self.auth
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("cb.auth.orchestrator.requests")
    def test_get_user(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = self.user
        mock_request.get.return_value = mock_response
        self.assertEqual(self.orch.get_user(), self.user)
        mock_request.get.assert_called_once_with(
            os.path.join(FAKE_API_URL, "user"), auth=self.auth
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("cb.auth.orchestrator.requests")
    def test_get_exchange_rate(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = self.exchange_rate
        mock_request.get.return_value = mock_response
        self.assertEqual(
            self.orch.get_exchange_rate(crypto_currency=Currency.BITCOIN),
            self.exchange_rate,
        )
        mock_request.get.assert_called_once_with(
            os.path.join(FAKE_API_URL, f"prices/{Currency.BITCOIN}-USD/buy"),
            auth=self.auth,
        )
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @patch("cb.auth.orchestrator.requests")
    def test_get_relative_exchange_rate(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = self.exchange_rate
        mock_request.get.return_value = mock_response
        self.assertEqual(
            self.orch.get_relative_exchange_rate(
                from_currency=Currency.BITCOIN,
                to_currency=Currency.ETHEREUM,
            ),
            1.0,
        )
        mock_request.get.assert_has_calls(
            [
                call(
                    os.path.join(FAKE_API_URL, f"prices/{Currency.BITCOIN}-USD/buy"),
                    auth=self.auth,
                ),
                call().raise_for_status(),
                call().json(),
                call(
                    os.path.join(FAKE_API_URL, f"prices/{Currency.ETHEREUM}-USD/buy"),
                    auth=self.auth,
                ),
                call().raise_for_status(),
                call().json(),
            ]
        )
        mock_response.raise_for_status.assert_called()
        mock_response.json.assert_called()


if __name__ == "__main__":
    unittest.main()
