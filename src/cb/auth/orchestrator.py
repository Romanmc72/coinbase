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
from .authenticator import CoinbaseApplicationAuth
from .authenticator import CoinbaseExchangeAuth
from .authenticator import Environment


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
        application_authenticator: CoinbaseApplicationAuth = None,
        exchange_authenticator: CoinbaseExchangeAuth = None,
    ) -> None:
        self.application_authenticator = (
            application_authenticator or CoinbaseApplicationAuth()
        )
        self.exchange_authenticator = exchange_authenticator or CoinbaseExchangeAuth()

    def _post_endpoint(
        self, endpoint: str, authenticator: CoinbaseAuth, body: dict = None
    ) -> dict:
        """
        use this to generate your various endpoint calls to post a json body
        and receive a json response
        """
        response = requests.post(
            os.path.join(authenticator.base_url, endpoint),
            auth=authenticator,
            json=body,
        )
        response.raise_for_status()
        return response.json()

    def _post_application(self, endpoint: str, body: dict = None) -> dict:
        """This endpoint is just for posting to the application api"""
        return self._post_endpoint(
            endpoint=endpoint, authenticator=self.application_authenticator, body=body
        )

    def _post_exchange(self, endpoint: str, body: dict = None) -> dict:
        """This endpoint is just for posting to the exchange api"""
        return self._post_endpoint(
            endpoint=endpoint, authenticator=self.exchange_authenticator, body=body
        )

    def _get_endpoint(self, endpoint: str, authenticator: CoinbaseAuth) -> dict:
        """use this to generate your various endpoint calls and return the json body"""
        response = requests.get(
            os.path.join(authenticator.base_url, endpoint), auth=authenticator
        )
        response.raise_for_status()
        return response.json()

    def _get_application(self, endpoint: str) -> dict:
        """This endpoint is just for getting from the application api"""
        return self._get_endpoint(
            endpoint=endpoint, authenticator=self.application_authenticator
        )

    def _get_exchange(self, endpoint: str) -> dict:
        """This endpoint is just for getting from the exchange api"""
        return self._get_endpoint(
            endpoint=endpoint, authenticator=self.exchange_authenticator
        )

    def get_accounts(self) -> dict:
        """Get the current accounts for this API Auth in JSON format"""
        return self._get_application("accounts")

    def get_user(self) -> dict:
        """Get the current user for this API Auth in JSON format"""
        return self._get_application("user")

    def get_exchange_rate(self, crypto_currency: Currency) -> float:
        """Get the exchange rate for a given crypto currency"""
        response = self._get_application(f"prices/{crypto_currency}-USD/buy")
        rate = float(response["data"]["amount"])
        return rate

    def get_wallets(self) -> dict:
        """Get all of the wallets in a dict with their names as the key"""
        wallets = {}
        data = self.get_accounts()
        for wallet in data["data"]:
            currency = wallet["currency"]["code"]
            wallets[currency] = wallet
        return wallets

    def get_wallet(self, crypto_currency: Currency) -> dict:
        """Grab a particular crypto wallet from the account"""
        return self.get_wallets().get(crypto_currency.value, {})

    def get_wallet_id(self, crypto_currency: Currency) -> dict:
        """Grab a particular crypto wallet id from the account"""
        return self.get_wallet(crypto_currency.value).get("id", {})

    def get_wallet_amount(self, crypto_currency: Currency) -> dict:
        """Grab a particular crypto wallet amount from the account"""
        return float(
            self.get_wallet(crypto_currency.value)
            .get("balance", {"amount": 0.0})
            .get("amount", 0.0)
        )

    def get_relative_exchange_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Get the exchange rate between 2 currencies"""
        from_c_to_usd = self.get_exchange_rate(from_currency)
        to_c_to_usd = self.get_exchange_rate(to_currency)
        from_c_to_to_c = from_c_to_usd / to_c_to_usd
        return from_c_to_to_c

    def trade_between_currencies(
        self, from_currency: Currency, to_currency: Currency, from_amount: float
    ) -> dict:
        """
        Description
        -----------
        Converts an amount of currency from one to another and returns the
        details of the trade.

        Params
        ------
        :from_currency: Currency
        The currency that will be traded in and converted.

        :to_currency: Currency
        What the from_currency will be converted to.

        :from_amount: float
        The amount of the from_currency to convert.

        Return
        ------
        dict
        Not sure exactly what to return yet. I will figure that out later.
        For now it returns the whole thing.
        """
        response = self._post_exchange(
            endpoint="conversions",
            body={
                "amount": str(from_amount),
                "from": from_currency.value,
                "to": to_currency.value,
            },
        )
        return response
