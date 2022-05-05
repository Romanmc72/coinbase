#!/usr/bin/env python3
"""Constants representing each currency we are interested in"""

from enum import Enum


class Currency(str, Enum):
    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    DOGE_COIN = "DOGE"
    US_DOLLAR_COIN = "USDC"
    USD = "USD"
