import logging
from pathlib import Path

import pytest

from tests.util import reset_db
import app
from lib import sql_util as db


TEST_LOG_FILE = Path(__file__).parent / 'logs/app.log'


@pytest.mark.integration
def test_check_coins():
    logging.getLogger().setLevel("INFO")
    reset_db()
    app.check_coins()

    with db.open_session() as test_session, test_session.begin():
        coins_in_db = test_session.query(db.Coin).all()
        assert len(coins_in_db) == 3
        prices_in_db = test_session.query(db.Price).all()
        assert len(prices_in_db) == 3

    with open(TEST_LOG_FILE, 'r') as fp:
        lines = fp.readlines()
        assert len(lines) >= 4 and "Portfolio:" in lines[-4]
        for line in lines[-3:]:
            assert "Owned=" in line and "Value=" in line and "Gains/Loss=" in line
