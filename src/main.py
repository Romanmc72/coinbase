#!/usr/bin/env python3
"""
Description
-----------
Tracks and triggers exchanges between ETH and BTC depending on the relative
exchange rate for the 2 currencies in order to profit from the relative
differences in their pricing over time.
"""
import logging
from datetime import datetime

from cb.auth.orchestrator import CoinbaseOrchestrator
from cb.currencies import Currency
from cb.logs.logger import get_logger
from db.client import DatabaseClient
from db.client import CURRENCY_FIELD_NAME
from db.client import PRICE_FIELD_NAME

ORCHESTRATOR = CoinbaseOrchestrator()
DB = DatabaseClient()

logger = get_logger(level=logging.INFO)


def main() -> None:
    """The main program to execute the tracking and trades together"""
    now = datetime.utcnow()

    currencies_to_pull = [
        Currency.ETHEREUM,
        Currency.BITCOIN,
        Currency.DOGE_COIN,
    ]

    for currency in  currencies_to_pull:
        logger.info(f"Pulling price for {currency}")
        current_price = ORCHESTRATOR.get_exchange_rate(currency)
        DB.write_crypto_price(currency, current_price, now)
        logger.info({
            CURRENCY_FIELD_NAME: currency, PRICE_FIELD_NAME: current_price
        })


if __name__ == "__main__":
    main()
