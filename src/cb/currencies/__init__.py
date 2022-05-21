#!/usr/bin/env python3
"""Constants representing each currency we are interested in"""

from cb.enums import StringEnum


class Currency(StringEnum):
    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    DOGE_COIN = "DOGE"
    US_DOLLAR_COIN = "USDC"
    USD = "USD"
