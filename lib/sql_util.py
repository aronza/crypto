import logging
import time
from urllib.parse import quote
from os import environ
from sqlalchemy import Column, String, DateTime, Float, create_engine, Integer
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, Session

from lib.util import LOG_LEVEL

Base = declarative_base()
ENGINE = None
DB_CONNECT_TIMEOUT = environ.get("DB_CONNECT_TIMEOUT", default=3)


def connect_mysql():
    logging.debug({"status": "CONNECTING", "component": "MySQL"})
    global ENGINE
    ENGINE = create_engine(f"mysql+pymysql://{quote(environ['DB_USERNAME'])}:{quote(environ['DB_PASSWORD'])}"
                           f"@{quote(environ['DB_HOST'])}:{environ['DB_PORT']}/{environ['DB_DATABASE']}",
                           connect_args={'connect_timeout': DB_CONNECT_TIMEOUT,
                                         'read_timeout': DB_CONNECT_TIMEOUT, 'write_timeout': DB_CONNECT_TIMEOUT},
                           echo=LOG_LEVEL == "DEBUG",
                           echo_pool=LOG_LEVEL == "DEBUG",
                           pool_timeout=DB_CONNECT_TIMEOUT,
                           pool_recycle=3600,
                           pool_pre_ping=True,
                           pool_use_lifo=True)
    connected = False
    while not connected:
        try:
            ENGINE.raw_connection().ping()
            connected = True
        except OperationalError as e:
            logging.info({"status": "RETRYING", "component": "MySQL"})
            time.sleep(1)
    logging.debug({"status": "SUCCESS", "component": "MySQL"})


def open_session():
    return Session(ENGINE)


class Coin(Base):
    __tablename__ = 't_coin'
    id = Column("c_id", String(16), primary_key=True)
    symbol = Column("c_symbol", String(16), nullable=False)
    name = Column("c_name", String(128), nullable=False)
    balance = Column("c_balance", Float, default=0)
    cost = Column("c_cost", Float, default=0)


class Price(Base):
    __tablename__ = 't_price_history'
    id = Column("c_id", Integer, primary_key=True)
    dateTime = Column("c_datetime", DateTime, nullable=False)
    coinId = Column("c_coin_id", String(16), nullable=False)
    price = Column("c_price", Float, nullable=False)


class Order(Base):
    __tablename__ = 't_order_history'
    id = Column("c_id", Integer, primary_key=True)
    dateTime = Column("c_datetime", DateTime, nullable=False)
    coinId = Column("c_coin_id", String(16), nullable=False)
    price = Column("c_price_filled", Float, nullable=False)

