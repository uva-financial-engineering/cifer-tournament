#!/usr/bin/env python

import sys

users_sql = """DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id serial NOT NULL,
  email text NOT NULL,
  password text NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO users (email, password) VALUES ('a@a.com', 'pbkdf2:sha1:1000$pVkEoJO4$82724b822cbcfb54c50122147c9f1e6b4dfed53c');"""

options_sql = """DROP TABLE IF EXISTS option_prices;
CREATE TABLE option_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock_id text NOT NULL,
    is_call boolean NOT NULL,
    strike numeric NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT option_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO option_prices (date, stock_id, is_call, strike, bid, ask)
VALUES """

stock_prices_sql = """DROP TABLE IF EXISTS stock_prices;
CREATE TABLE stock_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock_id text NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT stock_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stock_prices (date, stock_id, bid, ask)
VALUES """

stocks_sql = """DROP TABLE IF EXISTS stocks;
CREATE TABLE stocks (
    id serial NOT NULL,
    symbol text NOT NULL,
    CONSTRAINT stocks_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stocks (symbol)
VALUES """

transactions_sql = """DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    id serial NOT NULL,
    date date NOT NULL,
    user_id integer NOT NULL,
    stock_id text NOT NULL,
    is_buy boolean NOT NULL,
    qty numeric NOT NULL,
    CONSTRAINT transactions_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);"""

terrors_sql = """DROP TABLE IF EXISTS terrors;
CREATE TABLE terrors (
    id serial NOT NULL,
    date date NOT NULL,
    user_id integer NOT NULL,
    terror numeric NOT NULL,
    CONSTRAINT terrors_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);"""

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("-- Usage: python database.py [options CSV file] [stock prices CSV file]")
        exit(0)

    with open(sys.argv[1]) as f:
        options_csv = f.readlines()

    with open(sys.argv[2]) as f:
        stocks_csv = f.readlines()

    # Options

    iterlines = iter(options_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        options_sql += "('%s', '%s', %s, %s, %s, %s), " % ("-".join([date[2], date[0], date[1]]), pieces[1], "TRUE" if pieces[2] == "Call" else "FALSE", pieces[3], pieces[4], pieces[5])

    # Stock prices

    stocks = dict()

    iterlines = iter(stocks_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        stocks[pieces[1]] = None
        stock_prices_sql += "('%s', '%s', %s, %s), " % ("-".join([date[2], date[0], date[1]]), pieces[1], pieces[2], pieces[3])

    # Stocks

    for stock in sorted(stocks):
        stocks_sql += "('%s'), " % stock

    print(users_sql)
    print(transactions_sql)
    print(terrors_sql)
    print(options_sql[:-2] + ";")
    print(stock_prices_sql[:-2] + ";")
    print(stocks_sql[:-2] + ";")
