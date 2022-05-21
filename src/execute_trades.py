#!/usr/bin/env python3
"""
Description
-----------
Tracks and triggers exchanges between ETH and BTC depending on the relative
exchange rate for the 2 currencies in order to profit from the relative
differences in their pricing over time.
"""
# import json
import logging

from cb.auth.orchestrator import CoinbaseOrchestrator
from cb.currencies import Currency
from cb.logs.logger import get_logger

# from datetime import datetime


# from db.client import DatabaseClient
# from db.client import CURRENCY_FIELD_NAME
# from db.client import PRICE_FIELD_NAME

ORCHESTRATOR = CoinbaseOrchestrator()
# DB = DatabaseClient()

logger = get_logger(level=logging.INFO)


def execute_trades() -> None:
    """The main program to execute the tracking and trades together"""
    # logger.info(ORCHESTRATOR.get_wallet(Currency.ETHEREUM))
    # logger.info(ORCHESTRATOR.get_wallet(Currency.BITCOIN))
    
    ethereum_balance = ORCHESTRATOR.get_wallet_amount(Currency.ETHEREUM)
    # ethereum_balance = float(ORCHESTRATOR.get_exchange_wallet(Currency.ETHEREUM)['balance'])
    one_percent_of_balance = ethereum_balance * 0.01
    logger.info(f"Attempting to trade {one_percent_of_balance} of {Currency.ETHEREUM}")
    # logger.info(ORCHESTRATOR.get_exchange_accounts())
    trade = ORCHESTRATOR.transfer_between_currencies(
    # trade = ORCHESTRATOR.trade_between_currencies(
        Currency.ETHEREUM,
        Currency.BITCOIN,
        one_percent_of_balance,
    )
    logger.info(trade)
    # addresses = ORCHESTRATOR.get_or_create_address_for_currency(Currency.ETHEREUM)
    # logger.info(addresses)

    # now = datetime.utcnow()

    # currencies_to_pull = [
    #     Currency.ETHEREUM,
    #     Currency.BITCOIN,
    #     Currency.DOGE_COIN,
    # ]

    # for currency in currencies_to_pull:
    #     logger.info(f"Pulling price for {currency}")
    #     current_price = ORCHESTRATOR.get_exchange_rate(currency)
    #     DB.write_crypto_price(currency, current_price, now)
    #     logger.info({CURRENCY_FIELD_NAME: currency, PRICE_FIELD_NAME: current_price})


if __name__ == "__main__":
    execute_trades()
