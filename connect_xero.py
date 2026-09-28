import json
import os
import secrets
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"

# Read-only access to only the two reports we need
SCOPES = (
    "offline_access "
    "accounting.reports.profitandloss.read "
    "accounting.reports.balancesheet.read"
)

state = secrets.token_urlsafe(16)
result = {"code": None, "done": False}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        query = urllib.parse.parse_qs(parsed.query)
        if query.get("state", [None])[0] == state and "code" in query:
            result["code"] = query["code"][0]
            message = "Connected to Xero. You can close this tab and go back to VS Code."
        else:
            print("Xero returned an error:", query)
            message = "Something went wrong. Check the terminal."
        result["done"] = True

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode())

    def log_message(self, *args):
        pass  # keep the terminal clean


# 1. Open the Xero login page in the browser
auth_url = "https://login.xero.com/identity/connect/authorize?" + urllib.parse.urlencode({
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "state": state,
})
print("Opening Xero login in your browser...")
webbrowser.open(auth_url)

# 2. Wait for Xero to send us back to localhost:8080/callback
server = HTTPServer(("localhost", 8080), CallbackHandler)
while not result["done"]:
    server.handle_request()

if not result["code"]:
    raise SystemExit("No authorization code received. Stopping.")

# 3. Swap the code for access and refresh tokens
token_resp = requests.post(
    "https://identity.xero.com/connect/token",
    auth=(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": REDIRECT_URI,
    },
)
token_resp.raise_for_status()
tokens = token_resp.json()

# 4. Find out which Xero organisation we are connected to
conn_resp = requests.get(
    "https://api.xero.com/connections",
    headers={"Authorization": f"Bearer {tokens['access_token']}"},
)
conn_resp.raise_for_status()
connections = conn_resp.json()

print("\nConnected organisations:")
for c in connections:
    print(f"  - {c['tenantName']}")

tenant = next((c for c in connections if "Demo" in c["tenantName"]), connections[0])

# 5. Save everything for the next scripts
with open("tokens.json", "w") as f:
    json.dump({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "tenant_id": tenant["tenantId"],
        "tenant_name": tenant["tenantName"],
    }, f, indent=2)

print(f"\nDone. Using: {tenant['tenantName']}. Tokens saved to tokens.json")