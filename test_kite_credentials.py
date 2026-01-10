import os
from kiteconnect import KiteConnect

# Load API credentials from environment variables
API_KEY = os.environ.get("KITE_API_KEY")
ACCESS_TOKEN = os.environ.get("KITE_ACCESS_TOKEN")

if not API_KEY or not ACCESS_TOKEN:
    print("Error: KITE_API_KEY or KITE_ACCESS_TOKEN environment variables are not set.")
    print("Please set them before running this script:")
    print("export KITE_API_KEY=\"YOUR_KITE_API_KEY\"")
    print("export KITE_ACCESS_TOKEN=\"YOUR_KITE_ACCESS_TOKEN\"")
    exit(1)

try:
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(ACCESS_TOKEN)

    # Attempt to fetch user profile (a simple API call to verify credentials)
    profile = kite.profile()
    print("Successfully connected to KiteConnect and fetched user profile:")
    print(f"User ID: {profile.get('user_id')}")
    print(f"User Name: {profile.get('user_name')}")
    print("Your KiteConnect credentials are VALID.")

    # Attempt to fetch instruments to see if that's where the specific failure is
    print("\nAttempting to fetch instruments...")
    nifty = kite.ltp("NSE:SBIN")
    nifty_token = nifty["NSE:SBIN"]["instrument_token"]

    print("NIFTY 50 instrument token:", nifty_token)
    # for instrument in instruments:
    #     if instrument["exchange"] == "NSE" and instrument["tradingsymbol"] == "NIFTY 50" and instrument["instrument_type"] == "INDEX":
    #         nifty_token = instrument["instrument_token"]
    #         break

    if nifty_token:
        print(f"Successfully fetched NIFTY 50 instrument token: {nifty_token}")
    else:
        print("Failed to find NIFTY 50 instrument token in the fetched instruments.")
        print("This could be due to unexpected instrument data format or NIFTY 50 not being listed as expected.")
        print("Number of instruments fetched:", 1)


except Exception as e:
    print(f"Error connecting to KiteConnect or fetching data: {e}")
    print("Your KiteConnect credentials might be INVALID or expired, or there's a network issue.")
    print("Please ensure your KITE_API_KEY and KITE_ACCESS_TOKEN are correct and up-to-date.")
    exit(1)