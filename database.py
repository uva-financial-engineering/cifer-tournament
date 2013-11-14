#!/usr/bin/env python

import os
import sys

users_sql = """DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id serial NOT NULL,
  email text NOT NULL,
  password text NOT NULL,
  first_name text NOT NULL,
  last_name text NOT NULL,
  institution text NOT NULL,
  cash numeric NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO users (email, password, first_name, last_name, institution, cash) VALUES ('a@a.com', 'pbkdf2:sha1:1000$pVkEoJO4$82724b822cbcfb54c50122147c9f1e6b4dfed53c', 'John', 'Doe', 'University of Virginia', 18000000);"""

stocks_sql = """DROP TABLE IF EXISTS stocks;
CREATE TABLE stocks (
    id serial NOT NULL,
    symbol text NOT NULL,
    CONSTRAINT stocks_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stocks (symbol)
VALUES """

stock_prices_sql = """DROP TABLE IF EXISTS stock_prices;
CREATE TABLE stock_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock_id integer NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT stock_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stock_prices (date, stock_id, bid, ask)
VALUES """

option_prices_sql = """DROP TABLE IF EXISTS option_prices;
CREATE TABLE option_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock_id integer NOT NULL,
    is_call boolean NOT NULL,
    strike numeric NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT option_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO option_prices (date, stock_id, is_call, strike, bid, ask)
VALUES """

transactions_sql = """DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    id serial NOT NULL,
    date date NOT NULL,
    user_id integer NOT NULL,
    stock_id integer NOT NULL,
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

basket_items_sql = """DROP TABLE IF EXISTS basket_items;
CREATE TABLE basket_items (
    id serial NOT NULL,
    user_id integer NOT NULL,
    stock_id integer NOT NULL,
    is_call boolean NOT NULL,
    strike numeric NOT NULL,
    qty numeric NOT NULL,
    CONSTRAINT basket_items_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO basket_items (user_id, stock_id, is_call, strike, qty) VALUES
    (1, 5, FALSE, -1, 300000),
    (1, 5, TRUE, 12, 800000),
    (1, 5, TRUE, 12.5, 850000),
    (1, 11, FALSE, -1, 150000),
    (1, 11, FALSE, 12.5, 100000),
    (1, 11, FALSE, 13.5, 600000),
    (1, 11, FALSE, 14.5, 1000000),
    (1, 2, FALSE, -1, -5000),
    (1, 7, FALSE, -1, 100000),
    (1, 7, FALSE, 43, 2000000),
    (1, 12, FALSE, 68, 1000000),
    (1, 12, TRUE, 64, 700000),
    (1, 12, TRUE, 62, 450000),
    (1, 1, FALSE, -1, 800000);
"""

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("-- Usage: python database.py [options CSV file] [stock prices CSV file]")
        exit(0)
    elif len(sys.argv) > 3:
        with open("database.sql", "w") as f:
            f.write(users_sql +
                transactions_sql +
                terrors_sql +
                basket_items_sql)

        # Execute file

        os.system("PGPASSWORD=postgres psql -U postgres -d cifer -f database.sql")
        exit(0)

    with open(sys.argv[1]) as f:
        options_csv = f.readlines()

    with open(sys.argv[2]) as f:
        stocks_csv = f.readlines()

    # Stocks

    stocks = dict()

    iterlines = iter(stocks_csv)
    next(iterlines)

    for line in iterlines:
        stocks[line.strip().split(",")[1]] = None

    stock_id = 1
    for stock in sorted(stocks):
        stocks[stock] = stock_id;
        stocks_sql += "('%s'), " % stock
        stock_id += 1

    # Stock prices

    iterlines = iter(stocks_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        stock_prices_sql += "('%s', %d, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[1]], pieces[2], pieces[3])

    # Options

    iterlines = iter(options_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        option_prices_sql += "('%s', %d, %s, %s, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[1]], "TRUE" if pieces[2] == "Call" else "FALSE", pieces[3], pieces[4], pieces[5])

    # Write to SQL file

    with open("database.sql", "w") as f:
        f.write(users_sql +
            transactions_sql +
            terrors_sql +
            basket_items_sql +
            stocks_sql[:-2] + ";" +
            stock_prices_sql[:-2] + ";" +
            option_prices_sql[:-2] + ";")

    # Execute file

    os.system("PGPASSWORD=postgres psql -U postgres -d cifer -f database.sql")
