from datetime import datetime, timedelta

from pytest_mock import MockFixture

import app
from tests.util import reset_db
from lib import sql_util as db


def test_record_coin_price():
    reset_db()
    db.connect_mysql()

    test_session = db.open_session()
    test_session.begin()
    eth = db.Coin(id="eth", symbol="eth", name="ethereum")
    test_session.add(eth)
    test_session.add(db.Coin(id="usdt", symbol="usdt", name="tether", balance=786.687, cost=786))
    test_session.add(db.Price(coinId="eth", price=1405,
                              dateTime=(datetime.now() - timedelta(days=10)).isoformat(sep=' ', timespec='milliseconds')))
    test_session.add(db.Price(coinId="usdt", price=1.001, dateTime=datetime.now().isoformat(sep=' ', timespec='milliseconds')))
    test_session.commit()
    portfolio = {"eth": eth}
    btc_timestamp, eth_timestamp = datetime.now(), datetime.now()
    with db.open_session() as session, session.begin():
        app.record_coin_price(session, portfolio, "btc", "btc", "bitcoin", btc_timestamp, 20000)
        app.record_coin_price(session, portfolio, "eth", "eth", "ethereum", eth_timestamp, 2000)
        for key in ["btc", "eth"]:
            assert key in portfolio and portfolio[key].balance == 0 and portfolio[key].cost == 0

    test_session.commit()
    coins_in_db = test_session.query(db.Coin).all()
    assert len(coins_in_db) == 3
    for coin in coins_in_db:
        if coin.id == "btc":
            assert coin.name == "bitcoin" and coin.symbol == "btc"
            assert coin.balance == 0 and coin.cost == 0
        elif coin.id == "eth":
            assert coin.name == "ethereum" and coin.symbol == "eth"
            assert coin.balance == 0 and coin.cost == 0
        else:
            assert coin.id == "usdt" and coin.symbol == "usdt" and coin.name == "tether"
            assert coin.balance == 786.687 and coin.cost == 786

    prices_in_db = test_session.query(db.Price).all()
    assert len(prices_in_db) == 4
    for price in prices_in_db:
        if price.coinId == "btc":
            assert price.price == 20000 and price.dateTime.isoformat(timespec='seconds') == btc_timestamp.isoformat(
                timespec='seconds')
        elif price.coinId == "eth":
            if price.dateTime >= (datetime.today() - timedelta(days=1)):
                assert price.price == 2000 and price.dateTime.isoformat(timespec='seconds') == eth_timestamp.isoformat(
                    timespec='seconds')
            else:
                assert price.price == 1405
        else:
            assert price.coinId == "usdt" and price.price == 1.001
    test_session.close()


def test_trade_coin(mocker: MockFixture):
    reset_db()
    db.connect_mysql()

    test_session = db.open_session()
    test_session.begin()
    eth = db.Coin(id="eth", symbol="eth", name="ethereum")
    test_session.add(eth)
    portfolio = {"eth": eth}
    test_session.commit()

    mock_api = mocker.patch('app.crypto_api')
    mock_api.get_coin_price_history.return_value = [(i, 100) for i in range(10)]
    app.trade_coin(test_session, portfolio, "eth", "eth", 100)
    mock_api.submit_order.assert_not_called()

    mock_api.get_coin_price_history.return_value = [(i, 100 + i) for i in range(10)]
    mock_api.submit_order.return_value = 100.5
    app.trade_coin(test_session, portfolio, "eth", "eth", 100.5)
    mock_api.submit_order.assert_called_once()
    assert eth.balance == 1 and eth.cost == 100.5
    test_session.commit()

    orders_in_db = test_session.query(db.Order).all()
    assert len(orders_in_db) == 1
    assert orders_in_db[0].dateTime is not None and orders_in_db[0].coinId == "eth" and orders_in_db[0].price == 100.5
    test_session.close()


def test_check_coins(mocker: MockFixture):
    reset_db()

    mock_api = mocker.patch('app.crypto_api')
    mock_api.get_coins.return_value = [
        {"symbol": "btc", "id": "btc", "name": "bitcoin", "current_price": 20000, "last_updated": "2022-05-01T15:35:10.123456Z"},
        {"symbol": "eth", "id": "eth", "name": "ethereum", "current_price": 2000, "last_updated": "2022-05-01T15:35:11.123456Z"},
        {"symbol": "usdt", "id": "usdt", "name": "tether", "current_price": 1.007, "last_updated": "2022-05-01T15:35:09.123456Z"}]
    mock_api.get_coin_price_history.side_effect = [[(i, 20000 + i) for i in range(10)],
                                                   [(i, 2000 + i) for i in range(10)], [(i, 1.0 + i / 100) for i in range(10)]]
    mock_api.submit_order.side_effect = [20000, 2000, 1.007]
    app.check_coins()
    for coin_id, price in zip(["btc", "eth", "usdt"], [20000, 2000, 1.007]):
        mock_api.submit_order.assert_any_call(coin_id, 1, price)

    db.connect_mysql()
    test_session = db.open_session()
    test_session.begin()

    coins_in_db = test_session.query(db.Coin).all()
    assert len(coins_in_db) == 3
    for coin in coins_in_db:
        assert coin.balance == 1
        if coin.id == "btc":
            assert coin.name == "bitcoin" and coin.symbol == "btc" and coin.cost == 20000
        elif coin.id == "eth":
            assert coin.symbol == "eth" and coin.name == "ethereum" and coin.cost == 2000
        else:
            assert coin.id == "usdt" and coin.name == "tether" and coin.symbol == "usdt" and coin.cost == 1.007
    prices_in_db = test_session.query(db.Price).all()
    assert len(coins_in_db) == 3
    for price in prices_in_db:
        assert price.dateTime is not None
        if price.coinId == "btc":
            assert price.price == 20000
        elif price.coinId == "eth":
            assert price.price == 2000
        else:
            assert price.coinId == "usdt" and price.price == 1.007

    orders_in_db = test_session.query(db.Order).all()
    assert len(orders_in_db) == 3
    for order in orders_in_db:
        assert order.coinId in ["btc", "eth", "usdt"]
    test_session.close()

