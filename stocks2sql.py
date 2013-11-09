#!/usr/bin/env python

import fileinput

sql = """DROP TABLE IF EXISTS stock_prices;
CREATE TABLE stock_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock text NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT stock_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stock_prices (date, stock, bid, ask)
VALUES """

symbols_sql = """DROP TABLE IF EXISTS stocks;
CREATE TABLE stocks (
    id serial NOT NULL,
    symbol text NOT NULL,
    CONSTRAINT stocks_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO stocks (symbol)
VALUES """

if __name__ == "__main__":
    # Skip first line (column names) in CSV file
    iterlines = iter(fileinput.input())
    next(iterlines)

    symbols = dict()
    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        symbols[pieces[1]] = None
        sql += "('%s', '%s', %s, %s), " % ("-".join([date[2], date[0], date[1]]), pieces[1], pieces[2], pieces[3])

    for symbol in sorted(symbols):
        symbols_sql += "('%s'), " % symbol

    print(symbols_sql[:-2] + ";")
    print(sql[:-2] + ";")
