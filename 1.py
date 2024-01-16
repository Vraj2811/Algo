# from crypt import methods
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

# TRADER_PATH = ""
TRADER_PATH = "Vraj/"
LOCAL_HOLDINGS_PATH = TRADER_PATH + "user/holdings.csv"
LOCAL_REBUY_PATH = TRADER_PATH + "user/rebuy.csv"
LOCAL_TICKER_PATH = TRADER_PATH + "ticker_data.csv"

credentials_file = TRADER_PATH+"user/credentials.json"
with open(credentials_file, 'r') as json_file:
    credentials_data = json.load(json_file)

# Extract credentials from the JSON data
api_key = credentials_data.get("api_key")
api_secret = credentials_data.get("api_secret")

with open(TRADER_PATH+"user/access_token.json", 'r') as file:
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

z_holdings = kite.holdings()

print(z_holdings)

holdings_data = []
for holding in z_holdings:
    holdings_data.append([holding['instrument_token'], holding['tradingsymbol'],
                         holding['quantity'], holding['average_price']])

# holdings_data = []
# for holding in z_holdings:
#     holdings_data.append([holding['instrument_token'], holding['tradingsymbol'],
#                          holding['quantity'], holding['average_price'], holding['transaction_type']])

# Define the headers for the table
headers = ["Instrument Token", "Tradingsymbol", "Quantity", "Average Price"]
# headers = ["Instrument Token", "Tradingsymbol", "Quantity", "Average Price","B/S"]

# Print the table
print(tabulate(holdings_data, headers, tablefmt="pretty"))

order_id = kite.place_order(
    tradingsymbol="TATATECH",
    exchange=kite.EXCHANGE_NSE,
    transaction_type=kite.TRANSACTION_TYPE_SELL,
    quantity=1,
    variety=kite.VARIETY_REGULAR,  # Use VARIETY_REGULAR for regular orders, not AMO
    order_type=kite.ORDER_TYPE_MARKET,
    product=kite.PRODUCT_CNC,  # CNC for delivery-based equity trades
    validity=kite.VALIDITY_DAY
)


time.sleep(60)
print(tabulate(holdings_data, headers, tablefmt="pretty"))

# from pyotp import TOTP

# totp = TOTP("5KFKH5RE7VSUIKW464NVNHLZC2264WQU")
# totp_code = totp.now()

# print(totp_code)
