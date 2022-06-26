CREATE DATABASE IF NOT EXISTS crypto;

use crypto;

create table t_coin(
    c_id  VARCHAR(16) PRIMARY KEY,
    c_symbol VARCHAR(16) NOT NULL,
    c_name VARCHAR(128) NOT NULL,
    c_balance decimal(25,20) DEFAULT 0,
    c_cost decimal(25,20) DEFAULT 0
);

create table t_price_history(
c_id BIGINT AUTO_INCREMENT PRIMARY KEY,
c_datetime DATETIME(3) NOT NULL,
c_coin_id VARCHAR(16) NOT NULL,
c_price decimal(25,20) NOT NULL,

INDEX (c_datetime),
FOREIGN KEY (c_coin_id) REFERENCES t_coin(c_id)
);

create table t_order_history(
    c_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    c_datetime DATETIME(3) NOT NULL,
    c_coin_id VARCHAR(16) NOT NULL,
    c_price_filled decimal(25,20) NOT NULL,

INDEX (c_datetime),
FOREIGN KEY (c_coin_id) REFERENCES t_coin(c_id)
)