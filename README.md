# Coinbase

Coinbase is a crypto currency exchange where you can buy, sell, hold, and exchange crypto currencies. For managing your own wallet and only your own wallet programmatically they offer API Keys, and for accessing a multitude of wallets they offer Oauth2 protocols. Here in this repository I am interested in taking the very small sum of BTC and ETH that I own and coming up with a means by which I can instruct the computer to make trades between the two within my own account on my behalf to perform some form of price arbitrage to generate a profit. Let's see if this works.

## Example

The idea is pretty simple, if one of the 2 crypto currencies I am interested in goes down *relatively more* than the other one, then I will consider that currency to be "on sale" for the time being and transfer some fraction over to that currency. Or the same thing is true that if one currency went up *relatively more* than the other, I would consider it to have boomed and increased in value so that **the other one** is respectively "on sale". This should in theory create a ladder type of effect where by simply trading back and forth between the two I can ride them as they escalate one another across time like riding a wave of sorts. It is similar in theory to how this old school arcade game functions called "[Gravity Hill](https://www.youtube.com/watch?v=Xpzcpmk-TlY)". We will see if it actually works in practice.

## Also Neat

The nice things here are that:

1. Coinbase charges no fees on the exchange when crypto trades from one type to the other within the same account as long as it stays on the exchange
1. Both of the crypto currencies don't necessarily have to always be increasing for this strategy to consistently generate profit, they just must necessarily have imbalances between them over time at different amounts and at different times. (But if their exchange rate ever completely normalizes, then this strategy will crumble)

### Less Neat

Not as nice things:

1. Coinbase does charge for usage of the API above a certain amount.
1. Running servers is not always super cheap (unless you get your own hardware for free $$$ which I have some old desktops that I have converted to servers so that slaps).

## More context

I will just be using roughly $200 spread between BTC and ETH for this experiment which is pretty low stakes for me. I have a bachelors in Econ which I have yet to use since graduation +6 years ago, so this will be fun from that perspective.

## Using this Code

Head over to the `src/` directory and check things out from there. I am starting from scratch using this example code [here](https://developers.coinbase.com/docs/wallet/api-key-authentication) and the coinbase API docs online as of the time of writing this live [here](https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getaccounts). You can run the unit tests with the Makefile at the root of this repo, run `make test` to see the output.

### Setup

To use this as a library you can install it and create a Coinbase API Client to interact with the Coinbase API. You will simply need to have the environment variables set for `CB_API_KEY` and `CB_SECRET_KEY` to the values for your own coinbase account API keys, and you should allow your API keys to have read access to pretty much everything it can have read access to in order to hit certain endpoints. Be careful to never check your API keys into version control or store them in plaintext.

### Usage

I have created a few endpoint methods that I am interested in hitting, but there are some base methods you can extend to use `POST` or `GET` requests to hit other endpoints you are interested in.

Example code to get the current value of a particular cryptocurrency in USD.

```python
from cb.auth.orchestrator import CoinbaseOrchestrator
from cb.currencies import Currency

# This assumes you have the environment variables set correctly.
# If that is not you, import and pass in the auth object:
# >>> from cb.auth.authenticator import CoinbaseAuth
# >>> auth = CoinbaseAuth(api_key='*****', secret_key='*****')
# >>> orchestrator = = CoinbaseOrchestrator(authenticator=auth)
orchestrator = CoinbaseOrchestrator()

price = orchestrator.get_exchange_rate(currency=Currency.BITCOIN)

print(price)
```

That's it! I do have a `main.py` program and some other code here dedicated to interacting with influxdb to accomplish some of the goals I outlined above. So this repo will probably look more like a program than a useful library, but feel free to copy-paste things you find useful here. I might separate these pieces out into individual parts and server them as their own libraries. Who knows.
