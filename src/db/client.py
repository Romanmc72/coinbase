#!/usr/bin/env python3
"""
Description
-----------
This is supposed to be a really shitty and hacky little thing that will write
a buncha data to a local instance of influx, then read that data back in an
aggregated fashion. Ideally I can get a rolling average, but let's just make
sure we can stand this thing up and connect to it first...
"""
import json
import logging
import os
from datetime import datetime
from enum import Enum

import influxdb_client
from influxdb_client.client.flux_table import FluxStructureEncoder
from influxdb_client.client.write_api import SYNCHRONOUS

from cb.currencies import Currency

logger = logging.getLogger()

CURRENCY_FIELD_NAME = "currency"
PRICE_FIELD_NAME = "price"


class TimeUnit(str, Enum):
    MINUTES: "m"
    HOURS: "h"
    DAYS: "d"
    MONTHS: "mo"
    YEARS: "y"


class DatabaseClient(influxdb_client.InfluxDBClient):
    """
    Description
    -----------
    A wrapper around the influx db client that can be used to write and
    retrieve influx db data with relative ease. No need to memorize the new
    query syntax, just call the methods defined here and we will get to
    functionality we need.

    Params
    ------
    :bucket: str = None (default = ENV_VAR ${INFLUXDB_BUCKET})
    The bucket that this client will write to.

    :org: str = None (default = ENV_VAR ${INFLUXDB_ORG})
    The org that this bucket lives in.

    :token: str = None (default = ENV_VAR ${INFLUXDB_ADMIN_TOKEN})
    The admin token / API key that has read/write privileges to the above
    bucket and org.

    :url: str = None (default = ENV_VAR ${INFLUXDB_URL} OR https://localhost:8086)
    The url representing the influx database host and port.

    :ssl_ca_cert: str = None (default = ENV_VAR ${INFLUXDB_SSL_CA_CERT})
    The SSL certificate location of the on disk SSL cert used to encrypt data
    and verify the authenticity of the influx server

    :measurement_name: str = None (default = ENV_VAR ${INFLUXDB_MEASUREMENT_NAME})
    The name of the measurement you are going to write
    """

    def __init__(
        self,
        bucket: str = None,
        org: str = None,
        token: str = None,
        url: str = None,
        ssl_ca_cert: str = None,
        measurement_name: str = None,
    ):
        self.bucket = bucket or os.environ["INFLUXDB_BUCKET"]
        self.org = org or os.environ["INFLUXDB_ORG"]
        self.token = token or os.environ["INFLUXDB_ADMIN_TOKEN"]
        self.url = url or os.getenv("INFLUXDB_URL", "https://localhost:8086")
        self.ssl_ca_cert = ssl_ca_cert or os.environ["INFLUXDB_SSL_CA_CERT"]
        self.measurement_name = (
            measurement_name or os.environ["INFLUXDB_MEASUREMENT_NAME"]
        )
        super().__init__(
            url=self.url,
            token=self.token,
            org=self.org,
            # The default ssl settings didn't work, had to self sign
            ssl_ca_cert=self.ssl_ca_cert,
        )

    def write_crypto_price(
        self, currency: Currency, price: float, timestamp: datetime = None
    ) -> None:
        """
        Description
        -----------
        Write a certain crypto currency and price pair into influx either
        using the current timestamp or a timestamp override.

        Params
        ------
        :currency: Currency
        The currency identifier, e.g. BTC for Bitcoin.

        :price: float
        The price in terms of dollars.

        :timestamp: datetime = None (default = datetime.utcnow())
        The timestamp representing whe this price point is valid as of.

        Return
        ------
        None
        """
        ts = timestamp or datetime.utcnow()
        write_api = self.write_api(write_options=SYNCHRONOUS)
        data_point = (
            influxdb_client.Point(self.measurement_name)
            .tag(CURRENCY_FIELD_NAME, currency)
            .field(PRICE_FIELD_NAME, float(price))
            .time(
                ts,
                write_precision=influxdb_client.WritePrecision.MS,
            )
        )
        logger.debug(f"Writing {currency}, {price}, {ts}")
        write_api.write(bucket=self.bucket, org=self.org, record=data_point)

    def get_crypto_average_price(
        self, currency: Currency, window: int, time_unit: TimeUnit
    ) -> float:
        """
        Description
        -----------
        Pull the trailing average price for a given currency and a given time
        range.

        Params
        ------
        :currency: Currency
        The identifier for the crypto currency that you are interested in
        pulling the data for.

        :window: int
        The length of time to go back for.

        :time_unit: TimeUnit
        The time unit that relates to the window length.

        Return
        ------
        float
        The average price for the input currency and time expression.
        """
        query_api = self.query_api()

        query = f"""from(bucket:"{self.bucket}")
        |> range(start: -{window}{time_unit})
        |> filter(fn: (r) => r._measurement == "{self.measurement_name}")
        |> filter(fn: (r) => r.currency == "{currency}")
        |> filter(fn: (r) => r._field == "{PRICE_FIELD_NAME}") 
        |> aggregateWindow(every: inf, fn: mean)
        """
        logger.debug(f"Query: {query}")
        result = query_api.query(org=self.org, query=query)

        table = json.loads(json.dumps(result, cls=FluxStructureEncoder))
        logger.debug(table)
        avg_price = table[0]["records"][0]["values"]["_value"]

        return avg_price

    def write_trade_executed(
        self,
        from_currency: Currency,
        to_currency: Currency,
        from_amount: float,
        to_amount: float,
        price: float,
    ) -> None:
        """
        Description
        -----------
        Record a trade that was executed.

        Params
        ------
        :from_currency: Currency
        The currency identifier that the trade was from.

        :to_currency: Currency
        The currency that was traded to.

        :from_amount: float
        The amount that was traded from in terms of the from_currency.

        :to_amount: float
        The amount that was traded to in terms of the to_currency.

        :price: float
        The price recorded at the time of the trade.

        Return
        ------
        None
        """
        pass
