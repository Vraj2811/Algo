import time
import pandas as pd
from datetime import datetime, timedelta
import os
import shutil
import sys
from flask import Flask, request, send_file, render_template, flash, jsonify, make_response
from flask_cors import CORS
from kiteconnect import exceptions as kite_excp
from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from tabulate import tabulate

# Function to check if the market is open on a weekday (Monday to Friday)

credentials_file = "user/credentials.json"
with open(credentials_file, 'r') as json_file:
    credentials_data = json.load(json_file)

# Extract credentials from the JSON data
api_key = credentials_data.get("api_key")
api_secret = credentials_data.get("api_secret")

with open("user/access_token.json", 'r') as file:
    data_a = json.load(file)

# Get the current date in the format 'dd-mm-yy'
today_date = time.strftime('%d-%m-%y', time.localtime())

# Retrieve the access token for the current date
access_token = data_a[today_date]

all_tokens = None

kite = KiteConnect(api_key=api_key)
try:
    kite.set_access_token(access_token)
except Exception as e:
    print(e)
    print("Exiting the program due to Error.")
    sys.exit(0)


def is_market_open():
    current_time = datetime.now().time()
    current_day = datetime.now().weekday()

    # Check if it's a weekday (Monday to Friday)
    if 0 <= current_day <= 4:
        market_open_time = datetime.strptime("09:15:00", "%H:%M:%S").time()
        market_close_time = datetime.strptime("15:30:00", "%H:%M:%S").time()

        return market_open_time <= current_time <= market_close_time
    else:
        return False

# Function to perform trading strategy based on RSI


def perform_trading_strategy(instrument_token):
    file_name = f"ticker_data/{instrument_token}.csv"
    df = pd.read_csv(file_name)

    holdings_df = pd.read_csv("user/holdings.csv")

    rsi_threshold_low = 30
    rsi_threshold_high = 70

    rsi = df.tail(1)['RSI'].values[0]
    lp = df.tail(1)['last_price'].values[0]

    token_row = holdings_df.loc[holdings_df['token'] == int(instrument_token)]

    if rsi < rsi_threshold_low or lp > (1 + token_row['a_next_buy_perc'].values[0])/100*token_row['invested_money'].values[0]/token_row['quantity_owned'].values[0]:
        quantity_to_buy = token_row['a_quant_to_buy_perc'].values[0] * \
            token_row['quantity_owned'].values[0]

        order_id = kite.place_order(
            tradingsymbol=holdings_df['share_name'],
            exchange=kite.EXCHANGE_NSE,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=1,
            variety=kite.VARIETY_REGULAR,  # Use VARIETY_REGULAR for regular orders, not AMO
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_CNC,  # CNC for delivery-based equity trades
            validity=kite.VALIDITY_DAY
        )
        token_row['quantity_owned'] += 1
        token_row['invested_money'] += lp

    elif rsi > rsi_threshold_high or lp < (1 - token_row['b_stop_loss_perc'].values[0])/100*token_row['invested_money'].values[0]/token_row['quantity_owned'].values[0]:
        order_id = kite.place_order(
            tradingsymbol=holdings_df['share_name'],
            exchange=kite.EXCHANGE_NSE,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=1,
            variety=kite.VARIETY_REGULAR,  # Use VARIETY_REGULAR for regular orders, not AMO
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_CNC,  # CNC for delivery-based equity trades
            validity=kite.VALIDITY_DAY
        )

        token_row['quantity_owned'] -= 1
        token_row['invested_money'] -= lp

    holdings_df.to_csv("user/holdings.csv", index=False)


def algo_trader():
    while True:
        if is_market_open():
            holdings_file = "user/holdings.csv"

            holdings_df = pd.read_csv(holdings_file)
            instrument_tokens = holdings_df['instrument_token'].tolist()

            # Perform trading strategy for each token
            for instrument_token in instrument_tokens:
                perform_trading_strategy(instrument_token)

            time.sleep(60)
        else:
            print("Market is closed. Waiting for the next trading day...")
            current_time = datetime.now().time()
            next_trading_day = datetime.combine(datetime.now().date() + timedelta(days=1),
                                                datetime.strptime("09:15:00", "%H:%M:%S").time())
            time_until_next_trading_day = (
                next_trading_day - datetime.now()).total_seconds()

            time.sleep(time_until_next_trading_day)


if __name__ == "__main__":
    algo_trader()
