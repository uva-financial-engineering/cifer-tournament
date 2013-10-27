#!/usr/bin/env python

import fileinput

sql = """DROP TABLE IF EXISTS option_prices;
CREATE TABLE option_prices (
    id serial NOT NULL,
    date date NOT NULL,
    stock text NOT NULL,
    is_call boolean NOT NULL,
    strike numeric NOT NULL,
    bid numeric NOT NULL,
    ask numeric NOT NULL,
    CONSTRAINT option_prices_pkey PRIMARY KEY (id)
) WITH (OIDS=FALSE);
INSERT INTO option_prices (date, stock, is_call, strike, bid, ask)
VALUES """

if __name__ == "__main__":
    # Skip first line (column names) in CSV file
    iterlines = iter(fileinput.input())
    next(iterlines)

    for line in iterlines:
        pieces = line.strip().split(",")
        date = pieces[0].split("/")
        date[0] = "%02d" % int(date[0])
        date[1] = "%02d" % int(date[1])

        sql += "('%s', '%s', %s, %s, %s, %s), " % ("-".join([date[2], date[0], date[1]]), pieces[1], "TRUE" if pieces[2] == "Call" else "FALSE", pieces[3], pieces[4], pieces[5])

    print(sql[:-2] + ";")
