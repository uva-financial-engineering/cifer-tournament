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
  portfolio numeric NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO users (email, password, first_name, last_name, institution, cash, portfolio) VALUES ('a@a.com', 'pbkdf2:sha1:1000$pVkEoJO4$82724b822cbcfb54c50122147c9f1e6b4dfed53c', 'John', 'Doe', 'University of Virginia', 18000000, 47736625);"""

stocks_sql = """DROP TABLE IF EXISTS stocks;
CREATE TABLE stocks (
    id serial NOT NULL,
    symbol text NOT NULL,
    sector text NOT NULL,
    CONSTRAINT stocks_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stocks (symbol, sector)
VALUES """

asset_prices_sql = """DROP TABLE IF EXISTS asset_prices;
CREATE TABLE asset_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock_id integer NOT NULL,
    security smallint NOT NULL,
    strike numeric NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT asset_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO asset_prices (date, stock_id, security, strike, bid, ask)
VALUES """

transactions_sql = """DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    id serial NOT NULL,
    date date NOT NULL,
    user_id integer NOT NULL,
    is_buy boolean NOT NULL,
    stock_id integer NOT NULL,
    security smallint NOT NULL,
    strike numeric NOT NULL,
    qty numeric NOT NULL,
    value numeric NOT NULL,
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

portfolio_assets_sql = """DROP TABLE IF EXISTS portfolio_assets;
CREATE TABLE portfolio_assets (
    id serial NOT NULL,
    user_id integer NOT NULL,
    stock_id integer NOT NULL,
    security smallint NOT NULL,
    strike numeric NOT NULL,
    qty numeric NOT NULL,
    liquid boolean NOT NULL,
    CONSTRAINT portfolio_assets_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO portfolio_assets (user_id, stock_id, security, strike, qty, liquid) VALUES
    (1, 5, 0, -1, 300000, FALSE),
    (1, 5, 1, 12, 800000, FALSE),
    (1, 5, 1, 12.5, 850000, FALSE),
    (1, 11, 0, -1, 150000, FALSE),
    (1, 11, 2, 12.5, 100000, FALSE),
    (1, 11, 2, 13.5, 600000, FALSE),
    (1, 11, 2, 14.5, 1000000, FALSE),
    (1, 2, 0, -1, -5000, FALSE),
    (1, 7, 0, -1, 100000, FALSE),
    (1, 7, 2, 43, 2000000, FALSE),
    (1, 12, 2, 68, 1000000, FALSE),
    (1, 12, 1, 64, 700000, FALSE),
    (1, 12, 1, 62, 450000, FALSE),
    (1, 1, 0, -1, 800000, FALSE);
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
                portfolio_assets_sql)

        # Execute file

        os.system("sudo service postgresql restart")
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
        stocks_sql += "('%s', '-'), " % stock
        stock_id += 1

    # Stock prices

    iterlines = iter(stocks_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        asset_prices_sql += "('%s', %d, 0, -1, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[1]], pieces[2], pieces[3])

    # Options

    iterlines = iter(options_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        asset_prices_sql += "('%s', %d, %s, %s, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[1]], "1" if pieces[2] == "Call" else "2", pieces[3], pieces[4], pieces[5])

    # Write to SQL file

    with open("database.sql", "w") as f:
        f.write(users_sql +
            transactions_sql +
            terrors_sql +
            portfolio_assets_sql +
            stocks_sql[:-2] + ";" +
            asset_prices_sql[:-2] + ";")

    # Execute file

    os.system("sudo service postgresql restart")
    os.system("PGPASSWORD=postgres psql -U postgres -d cifer -f database.sql")
