import time
from datetime import datetime, timedelta
import pandas as pd
import os
import json
from kiteconnect import KiteTicker, KiteConnect
from datetime import datetime, timedelta

# Function to check if the market is open on a weekday (Monday to Friday)
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

# Function to save live data to CSV files
def save_live_data(live_data):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for instrument_token, data in live_data.items():
        data["timestamp"] = current_time
        file_name = f"Vraj/ticker_data/{instrument_token}.csv"
        df = pd.DataFrame([data])

        if not os.path.isfile(file_name):
            df.to_csv(file_name, index=False)
        else:
            df.to_csv(file_name, mode='a', header=False, index=False)

# Callback function to handle incoming ticks
def on_ticks(ws, ticks):
    for tick in ticks:
        instrument_token = tick["instrument_token"]
        close_price = tick["last_price"]

        if instrument_token not in last_close_prices:
            last_close_prices[instrument_token] = [close_price]
        else:
            last_close_prices[instrument_token].append(close_price)
            if len(last_close_prices[instrument_token]) > 14:
                last_close_prices[instrument_token].pop(0)

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
            "rsi": calculate_rsi(instrument_token, last_close_prices),
        }
        live_data[instrument_token] = data

# Callback function to handle the connection
def on_connect(ws, response):
    ws.subscribe(shares_interested)
    ws.set_mode(ws.MODE_FULL, shares_interested)

# Callback function to handle the closing of the WebSocket connection
def on_close(ws, code, reason):
    ws.stop()

# Main algorithm function
def algo_trader():
    while True:
        if is_market_open():
            print("Market is open. Performing trading strategy...")

            save_live_data()
            time.sleep(60)
        else:
            print("Market is closed. Waiting for the next trading day...")

            current_time = datetime.now().time()
            next_trading_day = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.strptime("09:15:00", "%H:%M:%S").time())
            time_until_next_trading_day = (next_trading_day - datetime.now()).total_seconds()

            time.sleep(time_until_next_trading_day)

if __name__ == "__main__":
    # Read API credentials and access token
    credentials_file = "Vraj/user/credentials.json"
    with open(credentials_file, 'r') as json_file:
        credentials_data = json.load(json_file)

    api_key = credentials_data.get("api_key")
    api_secret = credentials_data.get("api_secret")

    with open("Vraj/user/access_token.json", 'r') as file:
        data_a = json.load(file)

    today_date = time.strftime('%d-%m-%y', time.localtime())
    access_token = data_a[today_date]

    # Initialize Kite API and Ticker
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    holdings = pd.DataFrame(kite.holdings())
    shares_interested = holdings["instrument_token"].values.tolist()

    kws = KiteTicker(api_key, access_token)

    if not os.path.exists("Vraj/ticker_data"):
        os.makedirs("Vraj/ticker_data")

    live_data = {}
    last_close_prices = {}

    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    try:
        kws.connect(threaded=True)
        algo_trader()

    except KeyboardInterrupt:
        kws.stop()
        save_live_data()

    except Exception as e:
        print(e)
