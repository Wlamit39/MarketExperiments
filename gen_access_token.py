from kiteconnect import KiteConnect
import os

API_KEY = "n5r5fn7u84xxllmx"
API_SECRET =  "jfm8fwtu1hiak1ubih9ykpz12h1lz7ev"

kite = KiteConnect(api_key=API_KEY)

# Step 1: Get login URL
print("Login URL:")
print(kite.login_url())

# Step 2: After login, paste request_token here
request_token = input("Enter request_token from redirect URL: ")

# Step 3: Generate session
data = kite.generate_session(request_token, api_secret=API_SECRET)

access_token = data["access_token"]

print("Access Token:", access_token)

# Optional: set token for future API calls
kite.set_access_token(access_token)
