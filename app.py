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
# from tqdm import tqdm
import json
import time

TRADER_PATH = ""
LOCAL_HOLDINGS_PATH = TRADER_PATH + "user/holdings.csv"
LOCAL_REBUY_PATH = TRADER_PATH + "user/rebuy.csv"
LOCAL_TICKER_PATH = TRADER_PATH + "ticker_data.csv"

print("Configuring Kite..")
credentials_file = "credentials.json"
with open(credentials_file, 'r') as json_file:
    credentials_data = json.load(json_file)

# Extract credentials from the JSON data
api_key = credentials_data.get("api_key")
api_secret = credentials_data.get("api_secret")

with open("access_token.json", 'r') as file:
    data_a = json.load(file)

# Get the current date in the format 'dd-mm-yy'
today_date = time.strftime('%d-%m-%y', time.localtime())

# Retrieve the access token for the current date
access_token = data_a[today_date]

all_tokens = None


print("Initializing Kite API..")
kite = KiteConnect(api_key=api_key)
try:
    kite.set_access_token(access_token)
except Exception as e:
    print(e)
    print("Exiting the program due to Error.")
    sys.exit(0)

print("Kite API working.")
# Flask constructor
app = Flask(__name__)
CORS(app)
# A decorator used to tell the application
# which URL is associated function

################## AlgoTrader APIs ######################


@app.route("/get_orders", methods=["GET"])
def get_orders():
    local_path = TRADER_PATH + "user/orders.csv"
    return send_file(local_path, as_attachment=True)


@app.route("/get_interval_data", methods=["GET"])
def get_interval_data():
    local_path = TRADER_PATH + "user/interval_table.csv"
    return send_file(local_path, as_attachment=True)

################ Rebuy API #########################


@app.route("/get_rebuy_data", methods=["GET"])
def get_rebuy_data():
    local_path = LOCAL_REBUY_PATH
    return send_file(local_path, as_attachment=True)


@app.route('/set_rebuy', methods=['POST'])
def set_rebuy():
    if 'file' not in request.files:
        flash('No file part')
        # Create a JSON response with a 404 status code
        response_data = {"error": "File not selected"}
        response = make_response(jsonify(response_data), 404)
        return response

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        # Create a JSON response with a 404 status code
        response_data = {"error": "File not selected"}
        response = make_response(jsonify(response_data), 404)
        return response

    save_path = LOCAL_REBUY_PATH
    cp_path = TRADER_PATH + "user/old_rebuy.csv"

    if os.path.exists(cp_path):
        os.remove(cp_path)

    os.rename(save_path, cp_path)
    file.save(save_path)

    # Create a JSON response with a 200 status code
    response_data = {"message": "Rebuy File saved successfully"}
    response = make_response(jsonify(response_data), 200)
    return response


@app.route("/get_rebuy_details", methods=["POST"])
def get_rebuy_details():
    if request.headers.get("Content-Type") == "application/json":
        try:
            request_data = request.get_json()
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {
                "data": {}, "message": "Bad request | {}".format(e), "status": 500}
            response = make_response(jsonify(response_data), 500)
            return response

        name = str(request_data["r_name"])
        exchange = str(request_data["r_exchange"])

        # Load algotrader holdings.csv into a dataframe
        try:
            df_local_rebuy = pd.read_csv(LOCAL_REBUY_PATH)
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {"data": {
            }, "message": "Error loading local rebuy from CSV | " + str(e), "status": 500}
            response = make_response(jsonify(response_data), 500)
            return response

        # If the given stock is in algotrader holdings
        o = df_local_rebuy.loc[(df_local_rebuy["symbol"] == name) & (
            df_local_rebuy["exchange"] == exchange)].to_dict('records')
        if o:
            local_share_rebuy = o[0]
            data = {}
            data["base_price"] = local_share_rebuy["base_price"]
            data["rebuy_perc"] = local_share_rebuy["rebuy_perc"]
            data["rebuy_quant"] = local_share_rebuy["exit_perc"]
            data["exit_perc"] = local_share_rebuy["rebuy_quant"]

            # Create a JSON response with a 200 status code
            response_data = {
                "data": data, "message": "Successfully returned rebuy data.", "status": 200}
            response = make_response(jsonify(response_data), 200)
            return response
        else:
            # Create a JSON response with a 404 status code
            response_data = {"data": {}, "message": "Share {} | {} does not exist in algotrader rebuy CSV.".format(
                name, exchange, o), "status": 404}
            response = make_response(jsonify(response_data), 404)
            return response

    else:
        # Create a JSON response with a 500 status code
        response_data = {"data": {},
                         "message": "Incorrect headers.", "status": 500}
        response = make_response(jsonify(response_data), 500)
        return response


@app.route("/update_algotrader_rebuy", methods=["POST"])
def update_algotrader_rebuy():
    # Extract name and exchange from the request
    name = request.form.get("update_name").upper()
    exchange = request.form.get("update_exchange").upper()
    base_price = float(request.form.get("base_price"))
    rebuy_perc = int(request.form.get("update_rebuy_perc"))
    exit_perc = int(request.form.get("update_exit_perc"))
    rebuy_quant = int(request.form.get("update_rebuy_quant"))

    # Load algotrader holdings.csv into a dataframe
    try:
        df_local_rebuy = pd.read_csv(LOCAL_REBUY_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local rebuy details from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in algotrader holdings
    ind = df_local_rebuy.index[(df_local_rebuy['symbol'] == name) & (
        df_local_rebuy['exchange'] == exchange)].to_list()
    if ind:
        df_local_rebuy.loc[ind[0], "rebuy_perc"] = rebuy_perc
        df_local_rebuy.loc[ind[0], "rebuy_price"] = round(
            (base_price * (1 + rebuy_perc / 100)), 2)
        df_local_rebuy.loc[ind[0], "exit_perc"] = exit_perc
        df_local_rebuy.loc[ind[0], "exit_price"] = round(
            (base_price * (1 + exit_perc / 100)), 2)
        df_local_rebuy.loc[ind[0], "rebuy_quant"] = rebuy_quant

        # Add this in the df_local_holdings and save it
        try:
            df_local_rebuy.to_csv(LOCAL_REBUY_PATH, index=False)
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {
                "error": "Error in updating to algotrader holdings | {}".format(e)}
            response = make_response(jsonify(response_data), 500)
            return response

        # Create a JSON response with a 200 status code
        response_data = {
            "message": "Successfully updated the share in Algotrader."}
        response = make_response(jsonify(response_data), 200)
        return response
    else:
        # Create a JSON response with a 404 status code
        response_data = {
            "error": "Share not present in Algotrader holdings. Please add first."}
        response = make_response(jsonify(response_data), 404)
        return response


################ Holdings API #########################

@app.route('/get_holdings', methods=["GET"])
def get_holdings():
    """
    Return the holdings.csv file from the user folder.
    """
    local_path = LOCAL_HOLDINGS_PATH
    response = make_response(send_file(local_path, as_attachment=True))
    return response


@app.route('/set_holdings', methods=['POST'])
def set_holdings():
    if 'file' not in request.files:
        flash('No file part')
        # Create a JSON response with a 404 status code
        response_data = {"error": "File not selected"}
        response = make_response(jsonify(response_data), 404)
        return response

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        # Create a JSON response with a 404 status code
        response_data = {"error": "File not selected"}
        response = make_response(jsonify(response_data), 404)
        return response

    save_path = LOCAL_HOLDINGS_PATH
    cp_path = TRADER_PATH + "user/old_holdings.csv"
    if os.path.exists(cp_path):
        os.remove(cp_path)
    os.rename(save_path, cp_path)
    file.save(save_path)

    # Create a JSON response with a 200 status code
    response_data = {"message": "File saved successfully"}
    response = make_response(jsonify(response_data), 200)
    return response


@app.route('/get_zerodha_holdings', methods=["GET"])
def get_zerodha_holdings():
    """General method to return all the Zerodha holdings to the frontend.

    Returns:
        list of dict: z_holdings
    """
    try:
        # below is a list of dictionary
        z_holdings = kite.holdings()
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {"error": "Faced error calling Zerodha API: " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # Create a JSON response with a 200 status code
    response = make_response(jsonify(z_holdings), 200)
    return response


@app.route("/delete_share_from_trader", methods=["GET"])
def delete_share_from_trader():
    # Delete share from trader holdings
    name = request.args.get("z_share_name").upper()
    exchange = request.args.get("z_exchange").upper()
    try:
        df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local holdings from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    ind = df_local_holdings.index[(df_local_holdings['share_name'] == name) & (
        df_local_holdings['exchange'] == exchange)].to_list()
    token = df_local_holdings[(df_local_holdings['share_name'] == name) & (
        df_local_holdings['exchange'] == exchange)]["token"].values[0]
    df_local_holdings.drop(ind, axis=0, inplace=True)
    df_local_holdings.to_csv(LOCAL_HOLDINGS_PATH, index=False)

    # Delete share from rebuy csv
    try:
        df_rebuy_details = pd.read_csv(LOCAL_REBUY_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local rebuy from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    ind2 = df_rebuy_details.index[(
        df_rebuy_details['token'] == token)].to_list()
    if len(ind2) > 0:
        df_rebuy_details.drop(ind2, axis=0, inplace=True)
        df_rebuy_details.to_csv(LOCAL_REBUY_PATH, index=False)

    # Create a JSON response with a 200 status code
    response_data = {
        "message": "Share {} was deleted from Algotrader.".format(name)}
    response = make_response(jsonify(response_data), 200)
    return response


@app.route("/add_share_to_trader", methods=["GET"])
def add_share_to_trader():
    # Extract name and exchange from the request
    name = request.args.get("z_share_name").upper()
    exchange = request.args.get("z_exchange").upper()

    # Load algotrader holdings.csv into a dataframe
    try:
        df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local holdings from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in algotrader holdings
    out = df_local_holdings.loc[(df_local_holdings["share_name"] == name) & (
        df_local_holdings["exchange"] == exchange)].to_dict('records')
    if out:
        # Create a JSON response with a 500 status code
        response_data = {"error": "Share already present in Algotrader."}
        response = make_response(jsonify(response_data), 500)
        return response

    # Load zerodha holdings
    try:
        z_holdings = kite.holdings()
        df_z_holdings = pd.DataFrame(z_holdings)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {"error": "Faced error calling Zerodha API: " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in zerodha holdings
    out = df_z_holdings.loc[(df_z_holdings["tradingsymbol"] == name) & (
        df_z_holdings["exchange"] == exchange)].to_dict('records')
    z_share_holding = {}
    local_share_holding = {}

    if out:
        z_share_holding = out[0]

        # Add necessary data from z_holdings to local_holdings
        local_share_holding["token"] = z_share_holding["instrument_token"]
        local_share_holding["exchange"] = z_share_holding["exchange"]
        local_share_holding["share_name"] = z_share_holding["tradingsymbol"]
        local_share_holding["quantity_owned"] = z_share_holding["quantity"]
        local_share_holding["last_action"] = "_"
        # initialized with avg price
        local_share_holding["last_action_price"] = z_share_holding["average_price"]
        # initialized with total.
        local_share_holding["invested_money"] = round(
            z_share_holding["quantity"] * z_share_holding["average_price"], 2)
        local_share_holding["a_next_buy_perc"] = 15
        local_share_holding["a_quant_to_buy"] = 1
        local_share_holding["a_quant_to_buy_perc"] = 10
        local_share_holding["b_stop_loss_perc"] = 5
        # initialize
        local_share_holding["recent_high"] = z_share_holding["average_price"]
        local_share_holding["status"] = "TRACK"

        # Add this in the df_local_holdings and save it
        try:
            df_local_share_holding = pd.DataFrame(
                [local_share_holding], columns=df_local_holdings.columns)
            df_local_holdings = pd.concat(
                [df_local_holdings, df_local_share_holding], ignore_index=True)
            df_local_holdings.to_csv(LOCAL_HOLDINGS_PATH, index=False)
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {
                "error": "Error in adding to Algotrader holdings | {}".format(e)}
            response = make_response(jsonify(response_data), 500)
            return response

        # Create a JSON response with a 200 status code
        response_data = {
            "message": "Successfully saved the share in Algotrader. Status: TRACK"}
        response = make_response(jsonify(response_data), 200)
        return response
    else:
        # Create a JSON response with a 404 status code
        response_data = {
            "error": "Share of the given Exchange not present in Zerodha holdings. Please recheck name."}
        response = make_response(jsonify(response_data), 404)
        return response


@app.route("/get_holding_details", methods=["POST"])
def get_holding_details():
    if request.headers.get("Content-Type") == "application/json":
        try:
            request_data = request.get_json()
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {
                "data": {}, "message": "Bad request | {}".format(e), "status": 500}
            response = make_response(jsonify(response_data), 500)
            return response

        name = str(request_data["e_name"])
        exchange = str(request_data["e_exchange"])

        # Load algotrader holdings.csv into a dataframe
        try:
            df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {"data": {
            }, "message": "Error loading local holdings from CSV | " + str(e), "status": 500}
            response = make_response(jsonify(response_data), 500)
            return response

        # If the given stock is in algotrader holdings
        o = df_local_holdings.loc[(df_local_holdings["share_name"] == name) & (
            df_local_holdings["exchange"] == exchange)].to_dict('records')
        if o:
            local_share_holding = o[0]
            data = {}
            data["anbp"] = local_share_holding["a_next_buy_perc"]
            data["anbqp"] = local_share_holding["a_quant_to_buy_perc"]
            data["bsl"] = local_share_holding["b_stop_loss_perc"]

            # Create a JSON response with a 200 status code
            response_data = {
                "data": data, "message": "Successfully returned share data.", "status": 200}
            response = make_response(jsonify(response_data), 200)
            return response
        else:
            # Create a JSON response with a 404 status code
            response_data = {"data": {}, "message": "Share {} | {} does not exist in algotrader holdings.".format(
                name, exchange, o), "status": 404}
            response = make_response(jsonify(response_data), 404)
            return response

    else:
        # Create a JSON response with a 500 status code
        response_data = {"data": {},
                         "message": "Incorrect headers.", "status": 500}
        response = make_response(jsonify(response_data), 500)
        return response


@app.route("/update_algotrader_holding", methods=["POST"])
def update_algotrader_holding():
    # Extract name and exchange from the request
    name = request.form.get("update_name").upper()
    exchange = request.form.get("update_exchange").upper()
    anbp = int(request.form.get("update_anbp"))
    anbqp = int(request.form.get("update_anbqp"))
    bsl = int(request.form.get("update_bsl"))

    # Load algotrader holdings.csv into a dataframe
    try:
        df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local holdings from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in algotrader holdings
    ind = df_local_holdings.index[(df_local_holdings['share_name'] == name) & (
        df_local_holdings['exchange'] == exchange)].to_list()
    out = df_local_holdings.loc[(df_local_holdings["share_name"] == name) & (
        df_local_holdings["exchange"] == exchange)].to_dict('records')

    if out:
        local_share_holding = out[0]
        local_share_holding["a_next_buy_perc"] = anbp
        local_share_holding["a_quant_to_buy_perc"] = anbqp
        local_share_holding["b_stop_loss_perc"] = bsl

        # Add this in the df_local_holdings and save it
        try:
            # Drop the old row
            df_local_holdings.drop(index=ind, axis=0, inplace=True)
            # Append the new row
            df_local_share_holding = pd.DataFrame(
                [local_share_holding], columns=df_local_holdings.columns)
            df_local_holdings = pd.concat(
                [df_local_holdings, df_local_share_holding], ignore_index=True)
            df_local_holdings.to_csv(LOCAL_HOLDINGS_PATH, index=False)
        except Exception as e:
            # Create a JSON response with a 500 status code
            response_data = {
                "error": "Error in updating to Algotrader holdings | {}".format(e)}
            response = make_response(jsonify(response_data), 500)
            return response

        # Create a JSON response with a 200 status code
        response_data = {
            "message": "Successfully updated the share in Algotrader."}
        response = make_response(jsonify(response_data), 200)
        return response
    else:
        # Create a JSON response with a 404 status code
        response_data = {
            "error": "Share not present in Algotrader holdings. Please add first."}
        response = make_response(jsonify(response_data), 404)
        return response


@app.route("/check_status", methods=["GET"])
def check_status():
    # Extract name and exchange from the request
    name = request.args.get("z_share_name").upper()
    exchange = request.args.get("z_exchange").upper()

    # Load algotrader holdings.csv into a dataframe
    try:
        df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local holdings from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in algotrader holdings
    out = df_local_holdings.loc[(df_local_holdings["share_name"] == name) & (
        df_local_holdings["exchange"] == exchange)].to_dict('records')

    if out:
        # Create a JSON response with a 200 status code
        response_data = {"message": str(out[0]["status"])}
        response = make_response(jsonify(response_data), 200)
        return response
    else:
        # Create a JSON response with a 404 status code
        response_data = {
            "error": "{} | {} not in Algotrader holdings".format(name, exchange)}
        response = make_response(jsonify(response_data), 404)
        return response


@app.route("/toggle_status", methods=["GET"])
def toggle_status():
    # Extract name and exchange from the request
    name = request.args.get("z_share_name").upper()
    exchange = request.args.get("z_exchange").upper()

    # Load algotrader holdings.csv into a dataframe
    try:
        df_local_holdings = pd.read_csv(LOCAL_HOLDINGS_PATH)
    except Exception as e:
        # Create a JSON response with a 500 status code
        response_data = {
            "error": "Error loading local holdings from CSV | " + str(e)}
        response = make_response(jsonify(response_data), 500)
        return response

    # If the given stock is in algotrader holdings
    ind = df_local_holdings.index[(df_local_holdings['share_name'] == name) & (
        df_local_holdings['exchange'] == exchange)].to_list()

    if ind:
        status = df_local_holdings.loc[ind[0], "status"]
        if status == "TRACK":
            status = "UNTRACK"
        elif status == "UNTRACK":
            status = "TRACK"
        else:
            # Create a JSON response with a 500 status code
            response_data = {
                "error": "Can not toggle status: {}".format(status)}
            response = make_response(jsonify(response_data), 500)
            return response
    else:
        # Create a JSON response with a 404 status code
        response_data = {
            "error": "{} | {} not in Algotrader holdings".format(name, exchange)}
        response = make_response(jsonify(response_data), 404)
        return response

    # Change the status
    df_local_holdings.loc[ind[0], "status"] = status
    # Save it into the CSV
    df_local_holdings.to_csv(LOCAL_HOLDINGS_PATH, index=False)

    # Create a JSON response with a 200 status code
    response_data = {"message": "Status toggled to {}".format(status)}
    response = make_response(jsonify(response_data), 200)
    return response


#############################################################

if __name__ == '__main__':
    app.run('3.110.142.32', port=8080, debug=True)
