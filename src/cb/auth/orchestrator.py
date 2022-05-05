#!/usr/bin/env python3
"""
Description
-----------
This class is just a thin wrapper around the requests library to make it
easier to call the various endpoints in the Coinbase API that we care
about.
"""
import os

import requests

from ..currencies import Currency
from .authenticator import CoinbaseAuth

API_URL = "https://api.coinbase.com/v2/"


class CoinbaseOrchestrator:
    """
    Description
    -----------
    Hate memorizing a bunch of JSON body syntax and URL endpoints? Me too!
    I created this orchestrator to make managing various tasks requiring the
    Coinbase API much easier.

    Note:
    Currently just the API Keys are supported but this should be extendable in
    the future to leverage the Oauth2 protocol as well.

    Params
    ------
    :authenticator: CoinbaseAuth
    The instantiated coinbase authenticator from the module next door.

    :base_url: str = API_URL
    The base URL, defaults to the production endpoint but can be overwritten
    to leverage the sandbox endpoints as well.

    Usage
    -----
    Import this alongside the authenticator that you wish to use and then
    call your favorite Coinbase API endpoints with this orchestrator!

    e.g.
    ```python3
    >>> from cb.auth.authenticator import CoinbaseAuth
    >>> from cb.auth.orchestrator import CoinbaseOrchestrator
    >>> authenticator = CoinbaseAuth(api_key='...', secret_key='...')
    >>> orchestrator = CoinbaseOrchestrator(authenticator)
    >>> print(orchestrator.get_accounts())
    ```
    """

    def __init__(
        self,
        authenticator: CoinbaseAuth = None,
        base_url: str = None,
    ) -> None:
        self.authenticator = authenticator or CoinbaseAuth()
        self.base_url = base_url or API_URL

    def _post_endpoint(self, endpoint: str, body: dict = None) -> dict:
        """
        use this to generate your various endpoint calls to post a json body
        and receive a json response
        """
        response = requests.post(
            os.path.join(self.base_url, endpoint), auth=self.authenticator, body=body
        )
        response.raise_for_status()
        return response.json()

    def _get_endpoint(self, endpoint: str) -> dict:
        """use this to generate your various endpoint calls and return the json body"""
        response = requests.get(
            os.path.join(self.base_url, endpoint), auth=self.authenticator
        )
        response.raise_for_status()
        return response.json()

    def get_accounts(self) -> dict:
        """Get the current accounts for this API Auth in JSON format"""
        return self._get_endpoint("accounts")

    def get_user(self) -> dict:
        """Get the current user for this API Auth in JSON format"""
        return self._get_endpoint("user")

    def get_exchange_rate(self, crypto_currency: Currency) -> float:
        """Get the exchange rate for a given crypto currency"""
        response = self._get_endpoint(f"prices/{crypto_currency}-USD/buy")
        rate = float(response["data"]["amount"])
        return rate

    def get_relative_exchange_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Get the ETH/BTC exchange rate"""
        from_c_to_usd = self.get_exchange_rate(from_currency)
        to_c_to_usd = self.get_exchange_rate(to_currency)
        from_c_to_to_c = from_c_to_usd / to_c_to_usd
        return from_c_to_to_c
