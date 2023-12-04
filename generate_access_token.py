# Import necessary libraries
import os
import sys
import json
import datetime
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pyotp import TOTP
import time

# Load credentials from a JSON file
credentials_file = "user/credentials.json"
with open(credentials_file, 'r') as json_file:
    credentials_data = json.load(json_file)

# Extract credentials from the JSON data
api_key = credentials_data.get("api_key")
api_secret = credentials_data.get("api_secret")
zerodha_userid = credentials_data.get("zerodha_userid")
zerodha_pass = credentials_data.get("zerodha_pass")
zerodha_totp_key = credentials_data.get("zerodha_totp_key")

# Print a message indicating the access token retrieval process
print("---Getting Access Token---")

# Define the file path to store the access token
file_path = "user/access_token.json"

# Check if the access token file exists; if not, create an empty JSON object
if not os.path.exists(file_path):
    with open(file_path, 'w') as file:
        file.write('{}')

# Read the access token data from the file
with open(file_path, 'r') as file:
    data_a = json.load(file)

# Get the current date in the format 'dd-mm-yy'
today_date = time.strftime('%d-%m-%y', time.localtime())

# Check if the access token for the current date already exists, and exit if found
if today_date in data_a:
    access_token = data_a[today_date]
    exit()

# Initialize KiteConnect with your API key
kite = KiteConnect(api_key=api_key)

# Configure Selenium webdriver to use Chrome in headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")

# Create a WebDriver instance
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the Kite login URL
driver.get(kite.login_url())

# Wait for a few seconds to ensure the page is loaded
time.sleep(2)

# Find the username and password fields on the login page
username_field = driver.find_element(By.ID, "userid")
password_field = driver.find_element(By.ID, "password")

# Enter the Zerodha username and password
username_field.send_keys(zerodha_userid)
password_field.send_keys(zerodha_pass)

# Submit the login form by pressing Enter key
password_field.send_keys(Keys.RETURN)

# Wait for a few seconds
time.sleep(2)

# Create a TOTP (Time-Based One-Time Password) using the provided key
totp = TOTP(zerodha_totp_key)
totp_code = totp.now()

# Find the TOTP field on the page and enter the TOTP code
totp_field = driver.find_element(By.ID, "totp")
totp_field.send_keys(totp_code)

# Submit the TOTP form
totp_field.submit()

# Wait for a moment to ensure the login process is complete
time.sleep(10)

# Get the current URL after login
current_url = driver.current_url

# Extract the request token from the URL
request_token = current_url.split("request_token=")[1].split("&")[0]

# Close the WebDriver
driver.quit()

# Try to generate a session using the request token and API secret
try:
    data = kite.generate_session(
        request_token=request_token, api_secret=api_secret)
    access_token = data["access_token"]
    print("Login successful...")
except Exception as e:
    print(f"Login Failed: {str(e)}")
    sys.exit()

# Update the access token in the data dictionary for the current date
data_a[today_date] = access_token

# Write the updated data to the access token file
with open(file_path, 'w') as file:
    json.dump(data_a, file, indent=4)

# Print the API key and access token
print(f"API Key: {api_key}")
print(f"Access Token: {access_token}")

# Close the file
file.close()
