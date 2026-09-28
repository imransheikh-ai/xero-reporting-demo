import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
TOKEN_FILE = "tokens.json"


def _load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)


def _save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def refresh_tokens():
    """Get a fresh access token. Xero also gives a new refresh token each time, so we save it."""
    data = _load_tokens()
    resp = requests.post(
        "https://identity.xero.com/connect/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "refresh_token", "refresh_token": data["refresh_token"]},
    )
    resp.raise_for_status()
    new_tokens = resp.json()
    data["access_token"] = new_tokens["access_token"]
    data["refresh_token"] = new_tokens["refresh_token"]
    _save_tokens(data)
    return data


def get_report(report_name, params):
    """Fetch a Xero report, for example 'ProfitAndLoss' or 'BalanceSheet'."""
    data = refresh_tokens()
    resp = requests.get(
        f"https://api.xero.com/api.xro/2.0/Reports/{report_name}",
        headers={
            "Authorization": f"Bearer {data['access_token']}",
            "xero-tenant-id": data["tenant_id"],
            "Accept": "application/json",
        },
        params=params,
    )
    resp.raise_for_status()
    return resp.json()["Reports"][0], data["tenant_name"]