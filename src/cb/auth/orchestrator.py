#!/usr/bin/env python3
"""
Description
-----------
This class is just a thin wrapper around the requests library to make it
easier to call the various endpoints in the Coinbase API that we care
about.
"""
from locale import currency
import logging
import os
import uuid

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import HTTPError

from cb.auth.authenticator import (CoinbaseApplicationAuth, CoinbaseAuth,
                                   CoinbaseExchangeAuth, Environment)
from cb.currencies import Currency
from cb.enums import StringEnum

MAX_TRADING_PRECISION = 8
logger = logging.getLogger()


class Method(StringEnum):
    GET = "GET"
    POST = "POST"


class CoinbaseFormattingError(Exception):
    pass


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

    :retry_settings: HTTPAdapter = None (default = 3 retries for 50X errors)
    The HTTPAdapter settings to use for controlling retries on HTTP related errors.

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
        retry_settings: HTTPAdapter = None,
    ) -> None:
        self.application_authenticator = (
            application_authenticator or CoinbaseApplicationAuth()
        )
        self.exchange_authenticator = exchange_authenticator or CoinbaseExchangeAuth()
        self.retry_settings = retry_settings or HTTPAdapter(
            max_retries=Retry(
                total=3,
                backoff_factor=0.1,
                status_forcelist=[code for code in range(500, 511)],
            )
        )

    @staticmethod
    def check_trading_amount(
        amount: float, max_precision: int = MAX_TRADING_PRECISION
    ) -> float:
        """Check the trading amount against the max allowed precision"""
        if amount <= 0:
            raise CoinbaseFormattingError("amount must be > 0")

        # -2 because all floats start with '0.' then have the rest of the digits
        numeric_precision = len(str(float(amount % 1))) - 2

        if numeric_precision > max_precision:
            logger.info(f"Rounding from_amount, too precise: {amount}")
            final_amount = round(amount, max_precision)
        else:
            final_amount = amount

        return final_amount

    def _http_call(
        self,
        method: Method,
        endpoint: str,
        authenticator: CoinbaseAuth,
        body: dict = None,
    ):
        """Low level http call, do not use directly"""
        with requests.Session() as session:
            session.mount("https://", adapter=self.retry_settings)
            if method == Method.GET:
                response = session.get(
                    os.path.join(authenticator.base_url, endpoint),
                    auth=authenticator,
                )
            elif method == Method.POST:
                response = session.post(
                    os.path.join(authenticator.base_url, endpoint),
                    auth=authenticator,
                    json=body,
                )
            else:
                raise NotImplementedError(f"No method implemented for {method}")
        try:
            response.raise_for_status()
        except HTTPError as e:
            logger.critical(response.content.decode())
            raise e
        logger.debug(response.status_code)
        logger.debug(response.content.decode())
        return response.json()

    def _post_application(self, endpoint: str, body: dict = None) -> dict:
        """This endpoint is just for posting to the application api"""
        return self._http_call(
            method=Method.POST,
            endpoint=endpoint,
            authenticator=self.application_authenticator,
            body=body,
        )

    def _post_exchange(self, endpoint: str, body: dict = None) -> dict:
        """This endpoint is just for posting to the exchange api"""
        return self._http_call(
            method=Method.POST,
            endpoint=endpoint,
            authenticator=self.exchange_authenticator,
            body=body,
        )

    def _get_application(self, endpoint: str) -> dict:
        """This endpoint is just for getting from the application api"""
        return self._http_call(
            method=Method.GET,
            endpoint=endpoint,
            authenticator=self.application_authenticator,
        )

    def _get_exchange(self, endpoint: str) -> dict:
        """This endpoint is just for getting from the exchange api"""
        return self._http_call(
            method=Method.GET,
            endpoint=endpoint,
            authenticator=self.exchange_authenticator,
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
        return self.get_wallets().get(crypto_currency, {})

    def get_wallet_id(self, crypto_currency: Currency) -> dict:
        """Grab a particular crypto wallet id from the account"""
        return self.get_wallet(crypto_currency).get("id", {})

    def get_wallet_amount(self, crypto_currency: Currency) -> dict:
        """Grab a particular crypto wallet amount from the account"""
        return float(
            self.get_wallet(crypto_currency)
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

    def get_exchange_accounts(self) -> list:
        """Get all of the accounts for your coinbase pro profile"""
        return self._get_exchange("accounts")

    def get_exchange_wallets(self) -> dict:
        """Get all of the wallets for your coinbase pro profile keyed on currency"""
        wallets = {}
        accounts = self.get_exchange_accounts()
        for account in accounts:
            wallets[account['currency']] = account
        return wallets

    def get_exchange_wallet(self, currency: Currency) -> dict:
        return self.get_exchange_wallets().get(currency, {})

    def get_exchange_profiles(self) -> list:
        """Get all of the profiles for your coinbase pro api key"""
        return self._get_exchange("profiles")

    def get_exchange_default_profile(self) -> dict:
        """Get the default profile for your coinbase api key"""
        for profile in self.get_exchange_profiles():
            if profile["is_default"]:
                return profile
        return {}

    def get_exchange_default_profile_id(self) -> str:
        """Get the default profile id for your coinbase api key"""
        return self.get_exchange_default_profile().get("id", None)

    def transfer_between_currencies(
        self, from_currency: Currency, to_currency: Currency, from_amount: float
    ) -> dict:
        """
        Description
        -----------
        The exchange API has a "/conversions" endpoint but strangely does not
        let you do any conversions... I keep getting

        > {"message":"Cannot convert ETH to BTC"}

        and things like that. So back to the regular coinbase API to try and
        do this thing. I think transfers/transactions might be what I am
        looking for. We'll see.

        Params
        ------
        :from_currency: Currency
        The currency you are transferring from. (Your account for that currency will be used)

        :to_currency: Currency
        The currency you are transferring to. (Your account for that currency will be used)

        :from_amount: float
        The amount of the `from_currency` that you wish to transfer into the `to_currency`.
        """
        amount_to_send = self.check_trading_amount(from_amount)
        wallets = self.get_wallets()
        from_account = wallets[from_currency]["id"]
        to_account = wallets[to_currency]["id"]

        # This will prevent a retry from writing the same transaction several
        # times and transferring too much
        transaction_id = str(uuid.uuid4())
        logger.info({"transaction_id": transaction_id})

        return self._post_application(
            endpoint=f"accounts/{from_account}/transactions",
            body={
                "amount": str(amount_to_send),
                "currency": from_currency,
                "description": f"Trading {from_currency} to {to_currency} from the API.",
                "idem": transaction_id,
                "to": to_account,
                "type": "transfer",
            },
        )

    def trade_between_currencies(
        self,
        from_currency: Currency,
        to_currency: Currency,
        from_amount: float,
        profile_id: str = None,
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

        :profile_id: str = None (default = self.get_exchange_default_profile_id())
        The profile to execute these trades in.

        Return
        ------
        dict
        Not sure exactly what to return yet. I will figure that out later.
        For now it returns the whole thing.
        """
        amount = self.check_trading_amount(from_amount)

        response = self._post_exchange(
            endpoint="conversions",
            body={
                "profile_id": profile_id or self.get_exchange_default_profile_id(),
                "amount": str(amount),
                "from": from_currency,
                "to": to_currency,
            },
        )
        return response

    def get_or_create_address_for_currency(self, currency: Currency) -> str:
        """Given a currency, find your address!"""
        account_id = self.get_wallet_id(currency)
        stub = f"accounts/{account_id}/addresses"
        addresses = self._get_application(stub)["data"]
        if addresses:
            return addresses
        else:
            return self._post_application(stub, {"name": "default"})
