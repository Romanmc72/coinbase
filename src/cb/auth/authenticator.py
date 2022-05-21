#!/usr/bin/env python3
"""
Description
-----------
This module is meant to be imported and used in conjunction with the
orchestrator in order to call the API endpoints that you care about.
"""
import base64
import hashlib
import hmac
import logging
import os
import time
from abc import abstractmethod
from datetime import datetime

import requests
from requests.auth import AuthBase

from cb.enums import StringEnum

# DOCS: https://developers.coinbase.com/api/v2#introduction
APPLICATION_API_URL = "https://api.coinbase.com/v2/"
CB_API_KEY_ENV_VAR_NAME = "CB_API_KEY"
CB_SECRET_KEY_ENV_VAR_NAME = "CB_SECRET_KEY"

# DOCS: https://docs.cloud.coinbase.com/exchange/docs
EXCHANGE_API_URL = "https://api.exchange.coinbase.com/"
CB_EXCHANGE_API_KEY_ENV_VAR_NAME = "CB_EXCHANGE_API_KEY"
CB_EXCHANGE_SECRET_KEY_ENV_VAR_NAME = "CB_EXCHANGE_SECRET_KEY"
CB_EXCHANGE_PASSPHRASE_ENV_VAR_NAME = "CB_PASSPHRASE"

VAR_NOT_SET_MESSAGE = """ \
Coinbase `{arg_name}` not provided, please pass \
one in or set it in the ENV VAR {env_var_name}"""

logger = logging.getLogger()


class Environment(StringEnum):
    APPLICATION = "APPLICATION"
    EXCHANGE = "EXCHANGE"


class CoinbaseAuthException(Exception):
    pass


class CoinbaseAuth(AuthBase):
    """
    Description
    -----------
    The abstract class for various authenticator types. Do not import and use
    directly.

    Usage
    -----
    Like I said, don't. If the other authenticators do not meet your needs,
    inherit from this one to make a new one.
    """

    def __init__(
        self,
        environment: Environment,
        base_url: str,
        api_key_env_var: str,
        secret_key_env_var: str,
        passphrase_env_var: str = None,
        api_key: str = None,
        secret_key: str = None,
        passphrase: str = None,
    ):
        error_message = ""
        self.environment = environment
        self.base_url = base_url
        self.api_key_env_var = api_key_env_var
        self.secret_key_env_var = secret_key_env_var
        self.passphrase_env_var = passphrase_env_var
        self.api_key = api_key or os.getenv(self.api_key_env_var, None)
        self.secret_key = secret_key or os.getenv(self.secret_key_env_var, None)

        if self.passphrase_env_var:
            self.passphrase = passphrase or os.getenv(self.passphrase_env_var, None)
            if self.passphrase is None:
                error_message += VAR_NOT_SET_MESSAGE.format(
                    arg_name="passphrase", env_var_name=self.passphrase_env_var
                )
        else:
            self.passphrase = passphrase

        if self.api_key is None:
            error_message += VAR_NOT_SET_MESSAGE.format(
                arg_name="api_key", env_var_name=self.api_key_env_var
            )

        if self.secret_key is None:
            error_message += VAR_NOT_SET_MESSAGE.format(
                arg_name="secret_key", env_var_name=self.secret_key_env_var
            )

        if error_message:
            raise CoinbaseAuthException(error_message)

    def _generate_common_headers(
        self, request: requests.request, default_encoding: str = "utf8"
    ) -> dict:
        """
        Description
        -----------
        There are some common headers that both methods inherit from, this
        will generate it in either case and be available when inherited to
        keep the code more DRY.

        Params
        ------
        :request: requests.request
        The request from whom we get some of the required parameters for the
        hmac signature.

        :default_encoding: str = "utf8"
        The default encoding/decoding to use for strings.

        Return
        ------
        dict
        The headers common to any CoinbaseAuth type
        """

        timestamp = str(int(time.time()))

        message = (
            timestamp
            + request.method
            + request.path_url
            + (request.body.decode(default_encoding) if request.body else "")
        )

        if self.environment == Environment.APPLICATION:
            sk = self.secret_key.encode(default_encoding)
        elif self.environment == Environment.EXCHANGE:
            sk = base64.b64decode(self.secret_key)
        else:
            raise CoinbaseAuthException(
                f"Invalid environment selection {self.environment}"
            )

        hmac_signature = hmac.new(
            key=sk,
            msg=message.encode(default_encoding),
            digestmod=hashlib.sha256,
        )

        if self.environment == Environment.APPLICATION:
            signature = hmac_signature.hexdigest()
        elif self.environment == Environment.EXCHANGE:
            signature = base64.b64encode(hmac_signature.digest()).decode(default_encoding)
        else:
            raise CoinbaseAuthException(
                f"Invalid environment selection {self.environment}"
            )

        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
        }

    @abstractmethod
    def __call__(self, request: requests.request) -> requests.request:
        """Define your implementation specific to each subclass"""
        pass


class CoinbaseApplicationAuth(CoinbaseAuth):
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
        super().__init__(
            environment=Environment.APPLICATION,
            base_url=APPLICATION_API_URL,
            api_key_env_var=CB_API_KEY_ENV_VAR_NAME,
            secret_key_env_var=CB_SECRET_KEY_ENV_VAR_NAME,
            api_key=api_key,
            secret_key=secret_key,
        )

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
        updated_header = self._generate_common_headers(request)
        # Update this whenever you are ready to use a new version of the
        # API. According to coinbase, "Under no circumstance should you
        # always pass in the current date"
        # [source](https://developers.coinbase.com/api/v2#warnings)
        # This is the current version per the accounts page.
        updated_header["CB-VERSION"] = str(datetime(2022, 1, 17).date())
        request.headers.update(updated_header)

        return request


class CoinbaseExchangeAuth(CoinbaseAuth):
    """
    Description
    -----------
    Basically this functions exactly the same as the CoinbaseApplicationAuth class, but
    it has the added benefit of including required headers for the Exchange
    API (hint it needs a passphrase and doesn't care about the version)
    https://docs.cloud.coinbase.com/exchange/docs/authorization-and-authentication

    Params
    ------
    :api_key: str (default = environment variable)
    The Coinbase API Key to be used for your account.
    If not set within the script, will be selected from the environment for
    the variable 'CB_EXCHANGE_API_KEY' and if it is not set it will raise an error.

    :secret_key: str (default = environment variable)
    The Coinbase Secret Key to be used for your account.
    If not set within the script, will be selected from the environment for
    the variable 'CB_EXCHANGE_SECRET_KEY' and if neither is set it will raise an error.

    :passphrase: str (default = environment variables)
    The Coinbase API Key Passphrase you created when you created your EXCHANGE
    API Key. If you are not using the EXCHANGE environment setting, ignore
    this parameter.
    """

    def __init__(
        self, api_key: str = None, secret_key: str = None, passphrase: str = None
    ):
        super().__init__(
            environment=Environment.EXCHANGE,
            base_url=EXCHANGE_API_URL,
            api_key_env_var=CB_EXCHANGE_API_KEY_ENV_VAR_NAME,
            secret_key_env_var=CB_EXCHANGE_SECRET_KEY_ENV_VAR_NAME,
            passphrase_env_var=CB_EXCHANGE_PASSPHRASE_ENV_VAR_NAME,
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase,
        )

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
        updated_header = self._generate_common_headers(request)
        updated_header["CB-ACCESS-PASSPHRASE"] = self.passphrase

        request.headers.update(updated_header)

        return request
