from kiteconnect import KiteConnect
import pandas as pd
import time
from datetime import datetime

# ================= CONFIG ================= #
API_KEY = "n5r5fn7u84xxllmx"
ACCESS_TOKEN = "nee9xndy5pow5I7bnX3jpgmK4jvzlOzA"

OI_TRIGGER = 500          # % OI change
INTERVAL = 300            # 5 minutes
STRIKE_RANGE = 1          # ATM ± 1 strike
# ========================================= #

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)


def get_nifty_spot():
    return kite.ltp("NSE:NIFTY 50")["NSE:NIFTY 50"]["last_price"]


def get_option_chain():
    instruments = pd.DataFrame(kite.instruments("NFO"))
    df = instruments[
        (instruments["name"] == "NIFTY") &
        (instruments["segment"] == "NFO-OPT")
    ].copy()

    df["expiry"] = pd.to_datetime(df["expiry"])
    nearest_expiry = df["expiry"].min()   # 👈 nearest weekly expiry

    df = df[df["expiry"] == nearest_expiry]
    df["strike"] = df["strike"].astype(int)

    return df


def get_relevant_strikes(spot):
    atm = round(spot / 50) * 50
    return [atm + i * 50 for i in range(-STRIKE_RANGE, STRIKE_RANGE + 1)]


def snapshot(tokens):
    quotes = kite.quote(tokens)
    data = []
    for t, q in quotes.items():
        data.append({
            "token": t,
            "ltp": q["last_price"],
            "oi": q["oi"]
        })
    return pd.DataFrame(data)


def display_table(df, spot):
    df = df.copy()
    df["Signal"] = ""

    for i, r in df.iterrows():
        if r["oi_pct"] >= OI_TRIGGER and r["price_change"] < 0:
            df.at[i, "Signal"] = "🔥 SHORT"

    view = df[[
        "tradingsymbol",
        "instrument_type",
        "strike",
        "ltp",
        "price_change",
        "oi_pct",
        "Signal"
    ]]

    print("\n" + "=" * 75)
    print(f" Time: {datetime.now().strftime('%H:%M:%S')} | Spot: {round(spot,2)}")
    print("=" * 75)
    print(view.to_string(index=False))
    print("=" * 75)

    print(" 👉 ACTION SUGGESTED:")
    found = False
    for _, r in df.iterrows():
        if r["Signal"] == "🔥 SHORT":
            found = True
            if r["instrument_type"] == "CE":
                print(f" BUY {r['tradingsymbol'].replace('CE','PE')}")
            else:
                print(f" BUY {r['tradingsymbol'].replace('PE','CE')}")
    if not found:
        print(" No valid setup this cycle")
    print("-" * 75)


def track():
    spot = get_nifty_spot()
    strikes = get_relevant_strikes(spot)

    chain = get_option_chain()
    chain = chain[chain["strike"].isin(strikes)]

    tokens = list(chain["instrument_token"])

    snap1 = snapshot(tokens)
    time.sleep(INTERVAL)
    snap2 = snapshot(tokens)

    merged = snap2.merge(
        snap1, on="token", suffixes=("", "_prev")
    )

    merged["oi_pct"] = (
        (merged["oi"] - merged["oi_prev"]) /
        merged["oi_prev"]
    ) * 100

    merged["price_change"] = merged["ltp"] - merged["ltp_prev"]

    final = merged.merge(
        chain, left_on="token", right_on="instrument_token"
    )

    display_table(final, spot)


if __name__ == "__main__":
    print("🚀 NIFTY OI TRACKER STARTED (Manual Trading Mode)")
    print("⏱ Interval:", INTERVAL, "seconds")
    print("📌 OI Trigger:", OI_TRIGGER, "%")
    print("-" * 75)

    while True:
        try:
            track()
        except Exception as e:
            print("⚠ Error:", e)
            time.sleep(10)
