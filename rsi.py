import pandas as pd
import os
import json
from kiteconnect import KiteTicker, KiteConnect
import time
from datetime import datetime

# Define the path to the credentials file
credentials_file = "Vraj/user/credentials.json"

# Read the API key and API secret from the credentials JSON file
with open(credentials_file, 'r') as json_file:
    credentials_data = json.load(json_file)

api_key = credentials_data.get("api_key")
api_secret = credentials_data.get("api_secret")

# Read the access token data from a file
with open("Vraj/user/access_token.json", 'r') as file:
    data_a = json.load(file)

# Get the current date in the format 'dd-mm-yy'
today_date = time.strftime('%d-%m-%y', time.localtime())

# Retrieve the access token for the current date
access_token = data_a[today_date]

# Initialize the KiteConnect API client with the API key and access token
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Retrieve the holdings data and extract instrument tokens
holdings = pd.DataFrame(kite.holdings())
shares_interested = holdings["instrument_token"].values.tolist()

# Initialize the KiteTicker API client
kws = KiteTicker(api_key, access_token)

# Create a directory to store ticker data if it doesn't exist
if not os.path.exists("Vraj/ticker_data"):
    os.makedirs("Vraj/ticker_data")

# Create a dictionary to store live data and RSI
live_data = {}

# Dictionary to store last 'period' close prices for RSI calculation
last_close_prices = {}

# Function to calculate RSI
def calculate_rsi(instrument_token):
    close_prices = last_close_prices[instrument_token]
    period = 14  # You can adjust the period as needed

    if len(close_prices) > period:
        # Calculate daily price changes
        delta = pd.Series(close_prices).diff(1)

        # Calculate gain (positive changes) and loss (negative changes)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and average loss over the specified window
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        # Calculate the relative strength (RS)
        rs = avg_gain / avg_loss

        # Calculate the RSI using the formula
        rsi = 100 - (100 / (1 + rs))

        return rsi.values[-1]
    else:
        return None

# Define a function to save instrument-specific data to CSV files
def save_live_data():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for instrument_token, data in live_data.items():
        data["timestamp"] = current_time
        file_name = f"Vraj/ticker_data/{instrument_token}.csv"
        df = pd.DataFrame([data])

        if not os.path.isfile(file_name):
            # Create a new CSV file with headers for the first time
            df.to_csv(file_name, index=False)
        else:
            # Append data to existing CSV file
            df.to_csv(file_name, mode='a', header=False, index=False)

# Define a callback function to handle incoming ticks in "MODE_FULL"
def on_ticks(ws, ticks):
    for tick in ticks:
        instrument_token = tick["instrument_token"]
        close_price = tick["last_price"]

        # Update the last 'period' close prices for RSI calculation
        if instrument_token not in last_close_prices:
            last_close_prices[instrument_token] = [close_price]
        else:
            last_close_prices[instrument_token].append(close_price)
            if len(last_close_prices[instrument_token]) > 14:
                last_close_prices[instrument_token].pop(0)

        # Capture all available fields from the tick data
        data = {
            "timestamp": None,
            "last_price": close_price,
            "best_bid_price": tick["depth"]["buy"][0]["price"],
            "best_bid_quantity": tick["depth"]["buy"][0]["quantity"],
            "best_ask_price": tick["depth"]["sell"][0]["price"],
            "best_ask_quantity": tick["depth"]["sell"][0]["quantity"],
            "open_price": tick["ohlc"]["open"],
            "close_price": tick["ohlc"]["close"],
            "high_price": tick["ohlc"]["high"],
            "low_price": tick["ohlc"]["low"],
            "open_interest": tick["oi"],
            "rsi": calculate_rsi(instrument_token),
        }
        live_data[instrument_token] = data

# Modify your on_connect function to set "MODE_FULL" for instruments
def on_connect(ws, response):
    ws.subscribe(shares_interested)
    ws.set_mode(ws.MODE_FULL, shares_interested)

# Define a callback function to handle the closing of the WebSocket connection
def on_close(ws, code, reason):
    ws.stop()

# Set the callback functions for the KiteTicker client
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

try:
    # Connect to the Kite API in a separate thread
    kws.connect(threaded=True)

    while True:
        # Save live data every second
        save_live_data()
        time.sleep(1)

except KeyboardInterrupt:
    # Stop the WebSocket connection and save the final live data
    kws.stop()
    save_live_data()

except Exception as e:
    # Handle and log any exceptions that may occur
    print(e)
