import requests
import yaml
from datetime import date, datetime, timedelta
import yfinance as yf
import os
from dotenv import load_dotenv
import pandas as pd

# Load .env file
load_dotenv()


# === CONFIG FILE ===
CONFIG_FILE = "allocations.yml"   # YAML for allocations + account info

GHOSTFOLIO_URL = os.getenv("GHOSTFOLIO_URL")
API_KEY = os.getenv("API_KEY")

# === LOAD CONFIG ===
print(os.getcwd())
print("🔄 Loading configuration...")
with open(f"importapp/{CONFIG_FILE}", "r") as f:
    config = yaml.safe_load(f)

headers = {"Authorization": f"Bearer {API_KEY}"}

# === SANITY CHECKS ===
def validate_account(account):
    total_alloc = sum(account["holdings"].values())
    if not abs(total_alloc - 1.0) < 1e-6:
        raise ValueError(f"Allocations must sum to 1.0, got {total_alloc}")
    for ticker, pct in account["holdings"].items():
        if pct < 0:
            raise ValueError(f"Negative allocation for {ticker}")
    for contrib in account.get("contributions", []):
        if contrib["amount"] <= 0:
            raise ValueError(f"Contribution must be > 0 for {account['name']} on {contrib['date']}")
    print(f"✅ Config validated for {account['name']}")

for acct in config["accounts"]:
    validate_account(acct)

# === DATE NORMALIZATION ===
def normalize_trade_date(date_str: str) -> str:
    """
    Take a YYYY-MM-DD string, and if it's a weekend or holiday,
    roll it back to the last valid business day.
    """
    ts = pd.Timestamp(date_str)

    # If it's in the future, roll back to today
    today = pd.Timestamp.today().normalize()
    if ts > today:
        ts = today

    # If it's not a business day, roll back to the last one
    if not ts.isoweekday() in range(1, 6):  # Mon=1 … Fri=5
        ts = ts - pd.tseries.offsets.BDay(1)

    return ts.strftime("%Y-%m-%d")

# === PRICE FETCHER ===
def get_prices(tickers, tx_date=None):
    """
    Fetch prices for a list of tickers in one call.
    Returns dict {ticker: price}.
    """
    try:
        if tx_date:
            dt = datetime.strptime(tx_date, "%Y-%m-%d")
            data = yf.download(
                tickers,
                start=dt.strftime("%Y-%m-%d"),
                end=(dt + timedelta(days=1)).strftime("%Y-%m-%d"),
                group_by="ticker",
                progress=False
            )
            prices = {}
            for t in tickers:
                df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
                if not df.empty:
                    prices[t] = float(df["Close"].iloc[0])
            return prices
        else:
            data = yf.download(tickers, period="1d", group_by="ticker", progress=False)
            prices = {}
            for t in tickers:
                df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
                if not df.empty:
                    prices[t] = float(df["Close"].iloc[-1])
            return prices
    except Exception as e:
        raise RuntimeError(f"Batch price fetch failed: {e}")


# === BUILD TRANSACTIONS ===
def build_transactions(account, contribution, tx_date=None):
    transactions = []
    tickers = list(account["holdings"].keys())
    prices = get_prices(tickers, tx_date)
    for ticker, pct in account["holdings"].items():
        if ticker not in prices:
            print(f"⚠️ No price for {ticker} on {tx_date}, skipping")
            continue
        dollars = contribution * pct
        price = prices[ticker]
        shares = round(dollars / price, 4)
        transactions.append({
            "accountId": account["account_id"],
            "symbol": ticker,
            "type": "BUY",
            "quantity": shares,
            "unitPrice": price,
            "date": tx_date or date.today().isoformat(),
            "currency": account.get("currency", "USD"),
            "dataSource": "YAHOO",
            "fee": 0.0
        })
    return transactions

# === API POST ===
def post_transactions(transactions):
    payload = {"activities": transactions}
    r = requests.post(f"{GHOSTFOLIO_URL}/api/v1/import", json=payload, headers=headers, verify="importapp/rootcertchain.pem")
    if r.status_code == 201:
        for tx in transactions:
            print(f"✅ Added {tx['quantity']} shares of {tx['symbol']} "
                  f"on {tx['date']} @ {tx['unitPrice']}")
    else:
        print(f"❌ Error adding transactions: {r.text}")

# === MAIN ===
if __name__ == "__main__":
    for account in config["accounts"]:
        print(f"\n💼 Processing account: {account['name']}")
        for contrib in account.get("contributions", []):
            tx_date = normalize_trade_date(contrib["date"])
            amount = contrib["amount"]
            txs = build_transactions(account, amount, tx_date)
            post_transactions(txs)
