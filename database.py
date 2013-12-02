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
INSERT INTO users (email, password, first_name, last_name, institution, cash, portfolio) VALUES ('a@a.com', 'pbkdf2:sha1:1000$pVkEoJO4$82724b822cbcfb54c50122147c9f1e6b4dfed53c', 'John', 'Doe', 'University of Virginia', 18000000, 56041830);"""

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
    (1, 5, 0, -1, 250000, FALSE),
    (1, 5, 1, 14, 300000, FALSE),
    (1, 8, 1, 49, -100000, FALSE),
    (1, 8, 2, 55, 600000, FALSE),
    (1, 8, 2, 56, 1000000, FALSE),
    (1, 16, 1, 176, 1000000, FALSE),
    (1, 16, 1, 177, 300000, FALSE),
    (1, 2, 0, -1, -3000, FALSE),
    (1, 7, 1, 46, 200000, FALSE),
    (1, 7, 2, 50, -100000, FALSE),
    (1, 7, 2, 51, -50000, FALSE),
    (1, 29, 2, 96, 400000, FALSE),
    (1, 29, 2, 97, 500000, FALSE),
    (1, 29, 2, 98, 1000000, FALSE),
    (1, 13, 0, -1, 100000, FALSE),
    (1, 13, 1, 23, 400000, FALSE),
    (1, 13, 1, 24, 500000, FALSE),
    (1, 26, 1, 40, 500000, FALSE),
    (1, 26, 2, 43, 600000, FALSE),
    (1, 14, 1, 33, 600000, FALSE),
    (1, 14, 1, 34, 800000, FALSE),
    (1, 14, 1, 35, 1000000, FALSE),
    (1, 1, 0, -1, 400000, FALSE),
    (1, 1, 1, 8.5, -300000, FALSE),
    (1, 15, 0, -1, 3000, FALSE),
    (1, 17, 0, -1, 52000, FALSE);
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
        stocks[line.strip().split(",")[1]] = [None, line.strip().split(",")[2]]

    stock_id = 1
    for stock in sorted(stocks):
        stocks[stock][0] = stock_id;
        stocks_sql += "('%s', '%s'), " % (stock, stocks[stock][1])
        stock_id += 1

    # Stock prices

    iterlines = iter(stocks_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        asset_prices_sql += "('%s', %d, 0, -1, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[1]][0], "%.2f" % float(pieces[3]), "%.2f" % float(pieces[4]))

    # Options

    iterlines = iter(options_csv)
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        asset_prices_sql += "('%s', %d, %s, %s, %s, %s), " % ("-".join([date[2], date[0], date[1]]), stocks[pieces[2]][0], "1" if pieces[3] == "Call" else "2", pieces[4], "%.2f" % float(pieces[5]), "%.2f" % float(pieces[6]))

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
