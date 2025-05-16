import requests
import json
from base64 import b64encode

RPC_USER = "bitcoinrpc"
RPC_PASSWORD ="password"
RPC_PORT = 18443

def rpc_call(method, params=None):
    url = f"http://127.0.0.1:{RPC_PORT}/"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + b64encode(f"{RPC_USER}:{RPC_PASSWORD}".encode()).decode()
    }
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "bitcli",
        "method": method,
        "params": params or []
    })
    response = requests.post(url, headers=headers, data=payload)
    print("Status code:", response.status_code)
    print("Raw response:", response.text)
    response.raise_for_status()
    return response.json()["result"]


