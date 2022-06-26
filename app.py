"""Crypto Interview Assessment Module."""
from datetime import datetime
import logging
from operator import itemgetter
from os import environ
from apscheduler.schedulers.blocking import BlockingScheduler

from dotenv import find_dotenv, load_dotenv

from lib import sql_util as db, crypto_api
from lib.util import setup_logger

APP_ENV = environ.get("APP_ENV")
load_dotenv(find_dotenv(filename=".env." + APP_ENV if APP_ENV else ".env", raise_error_if_not_found=True))
setup_logger()
db.connect_mysql()
scheduler = BlockingScheduler()
TOP_N_COINS = int(environ.get("APP_TOP_N_COINS", default=3))
ORDER_AMOUNT = int(environ.get("APP_ORDER_AMOUNT", default=1))


# Start Here
def record_coin_price(session, portfolio, coin_id, symbol, name, price_time, price):
    if coin_id not in portfolio:
        coin_definition = db.Coin(id=coin_id, symbol=symbol, name=name)
        session.add(coin_definition)
        portfolio[coin_id] = coin_definition
        session.flush()
    session.add(db.Price(dateTime=price_time.isoformat(sep=' '), coinId=coin_id, price=price))


def trade_coin(session, portfolio, coin_id, symbol, price):
    prices = crypto_api.get_coin_price_history(coin_id)
    if not prices:
        logging.error(f"Failed to fetch prices for coin_id: {coin_id}")
        return
    moving_average = sum([price for _, price in prices]) / len(prices)
    if price < moving_average:
        order_time = datetime.now().isoformat(sep=' ')
        price_filled = crypto_api.submit_order(coin_id, ORDER_AMOUNT, price)
        logging.info(f"Order filled for {ORDER_AMOUNT} {symbol} at {price_filled}")
        session.add(db.Order(dateTime=order_time, coinId=coin_id, price=price_filled))
        portfolio[coin_id].balance += ORDER_AMOUNT
        portfolio[coin_id].cost += ORDER_AMOUNT * price_filled
    else:
        logging.info(f"Ignoring {symbol} as price {price} is higher or equal to average {moving_average}")


# If our portfolio includes coins, we didn't fetch the price for in the first API Call
def fetch_missing_prices(portfolio, prices):
    missing_prices = [coin_id for coin_id in portfolio if coin_id not in prices]
    if missing_prices:
        for coin in crypto_api.get_coins(missing_prices):
            prices[coin["id"]] = coin["current_price"]


def log_portfolio(portfolio, prices):
    fetch_missing_prices(portfolio, prices)
    logging.info("Portfolio:")
    for coin_id, coin in portfolio.items():
        balance, cost, value = coin.balance, coin.cost, coin.balance * prices[coin_id]
        profit = (value - cost) / cost if cost > 0 else 0
        logging.info(f"{coin.symbol.upper()}:\tOwned={balance}\tValue={value}\tGains/Loss={profit:.2f}%")


@scheduler.scheduled_job('interval', hours=1)
def check_coins():
    logging.info("Checking coin prices")
    with db.open_session() as session, session.begin():
        portfolio = {coin.id: coin for coin in session.query(db.Coin).all()}
        coins = crypto_api.get_coins()
        if not coins:
            logging.error(f"Failed to fetch coins from API")
            return
        coin_prices = {coin['id']: coin['current_price'] for coin in coins}
        for coin in coins[:TOP_N_COINS]:
            coin_id, symbol, name, price, last_updated = itemgetter('id', 'symbol', 'name', 'current_price', 'last_updated')(coin)
            price_time = datetime.fromisoformat(last_updated[:-1])

            record_coin_price(session, portfolio, coin_id, symbol, name, price_time, price)
            trade_coin(session, portfolio, coin_id, symbol, price)

        log_portfolio(portfolio, coin_prices)


if __name__ == "__main__":
    check_coins()
    scheduler.start()
