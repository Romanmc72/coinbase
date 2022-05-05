#!/usr/bin/env python3
"""
Description
-----------
This module is meant to be imported and used in conjunction with the
orchestrator in order to call the API endpoints that you care about.
"""
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime

import requests
from requests.auth import AuthBase

logger = logging.getLogger()

CB_API_KEY_ENV_VAR_NAME = "CB_API_KEY"
CB_SECRET_KEY_ENV_VAR_NAME = "CB_SECRET_KEY"

VAR_NOT_SET_MESSAGE = """ \
Coinbase `{arg_name}` not provided, please pass \
one in or set it in the ENV VAR {env_var_name}"""


class CoinbaseAuthException(Exception):
    pass


class CoinbaseAuth(AuthBase):
    """
    Description
    -----------
    Authorize to the Coinbase API using the methods laid out here
    https://developers.coinbase.com/docs/wallet/api-key-authentication
    in order to make API calls to the Coinbase API service on behalf of
    your own Coinbase account.

    Params
    ------
    :api_key: str (default = environment variable)
    The Coinbase API Key to be used for your account.
    If not set within the script, will be selected from the environment for
    the variable 'CB_API_KEY' and if neither is set it will raise an error.

    :secret_key: str (default = environment variable)
    The Coinbase Secret Key to be used for your account.
    If not set within the script, will be selected from the environment for
    the variable 'CB_SECRET_KEY' and if neither is set it will raise an error.

    Usage
    -----
    This class should be instantiated and used as the `auth` parameter in a
    python requests request to the API.

    e.g. (just don't save passwords in plaintext please)
    ```python3
    >>> # This will fetch the current user associated to the API Key and
    >>> # Secret Key pair and print the results
    >>> import requests
    >>> from cb.auth import CoinbaseAuth
    >>> from cb.auth import API_URL
    >>> auth = CoinbaseAuth(api_key='...', secret_key='...')
    >>> users_endpoint = API_URL + 'user'
    >>> request = requests.get(users_endpoint, auth=auth)
    >>> print(response.json())
    ```
    """

    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.getenv(CB_API_KEY_ENV_VAR_NAME, None)
        self.secret_key = secret_key or os.getenv(CB_SECRET_KEY_ENV_VAR_NAME, None)
        error_message = ""
        if self.api_key is None:
            error_message += VAR_NOT_SET_MESSAGE.format(
                arg_name="api_key",
                env_var_name=CB_API_KEY_ENV_VAR_NAME,
            )
        if self.secret_key is None:
            error_message += VAR_NOT_SET_MESSAGE.format(
                arg_name="secret_key",
                env_var_name=CB_SECRET_KEY_ENV_VAR_NAME,
            )
        if error_message:
            raise CoinbaseAuthException(error_message)

    def __call__(self, request: requests.request) -> requests.request:
        """
        Description
        -----------
        This is the __call__ method that is implicitly called when you pass
        the AuthBase object to a requests method using the auth parameter. It
        will perform the necessary actions to update the request's headers
        with the appropriate details to authenticate the request.

        Params
        ------
        :request: requests.request
        This is set whenever this authorizer is used to authenticate a
        request with the requests library, you do not need to set this.

        Return
        ------
        requests.request
        Returns the original request, but with the correct header details.
        """
        timestamp = str(int(time.time()))
        message = timestamp + request.method + request.path_url + (request.body or "")
        logger.debug(message)
        signature = hmac.new(
            key=self.secret_key.encode("utf8"),
            msg=message.encode("utf8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        logger.debug(signature)
        updated_header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            # Update this whenever you are ready to use a new version of the
            # API. According to coinbase, "Under no circumstance should you
            # always pass in the current date"
            # [source](https://developers.coinbase.com/api/v2#warnings)
            # This is the current version per the accounts page.
            "CB-VERSION": str(datetime(2022, 1, 17).date()),
        }
        logger.debug(updated_header)
        request.headers.update(updated_header)

        return request
