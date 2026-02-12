#!/usr/bin/env python3
"""
x402 Middleware - Payment + Token Gating for Oracle Sentinel API
"""
import json
import os
from functools import wraps
from flask import request, jsonify, Response
from token_gating import check_osai_holder

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'x402_config.json')
_config = None

def get_config():
    global _config
    if _config is None:
        with open(CONFIG_PATH, 'r') as f:
            _config = json.load(f)
    return _config

def get_endpoint_price(method: str, path: str) -> int:
    config = get_config()
    endpoint_key = f"{method} {path}"
    if endpoint_key in config["pricing"]:
        return config["pricing"][endpoint_key]
    for key, price in config["pricing"].items():
        key_parts = key.split()
        if len(key_parts) == 2:
            key_method, key_path = key_parts
            if key_method == method:
                base_path = key_path.split('<')[0].rstrip('/')
                if path.startswith(base_path):
                    return price
    return 10000

def create_payment_requirements() -> dict:
    config = get_config()
    method = request.method
    path = request.path
    price = get_endpoint_price(method, path)
    return {
        "x402Version": 2,
        "accepts": [{
            "scheme": "exact",
            "network": config["network_string"],
            "maxAmountRequired": str(price),
            "asset": config["usdc_mint"],
            "payTo": config["treasury_wallet"],
            "extra": {
                "facilitator": config["facilitator_url"],
                "feePayer": "2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
                "description": f"Oracle Sentinel API: {method} {path}",
                "mimeType": "application/json",
                "resource": f"https://oraclesentinel.xyz{path}"
            }
        }],
        "error": "Payment required",
        "alternatives": {
            "token_gating": {
                "token": "$OSAI",
                "mint": config["osai_mint"],
                "min_balance": config["token_gating"]["min_balance"],
                "benefit": "Free unlimited API access (signature required)"
            }
        }
    }

def verify_and_settle_payment(payment_header: str) -> tuple:
    import requests
    config = get_config()
    price = get_endpoint_price(request.method, request.path)
    try:
        verify_response = requests.post(
            f"{config['facilitator_url']}/verify",
            json={
                "x402Version": 2,
                "payment": payment_header,
                "paymentRequirements": {
                    "scheme": "exact",
                    "network": config["network_string"],
                    "maxAmountRequired": str(price),
                    "asset": config["usdc_mint"],
                    "payTo": config["treasury_wallet"]
                }
            },
            timeout=30
        )
        if verify_response.status_code == 200:
            result = verify_response.json()
            if result.get("valid") or result.get("isValid"):
                requests.post(
                    f"{config['facilitator_url']}/settle",
                    json={"x402Version": 2, "payment": payment_header},
                    timeout=30
                )
                return True, "settled"
            return False, result.get("error", "Invalid payment")
        return False, f"Facilitator error: {verify_response.status_code}"
    except Exception as e:
        return False, str(e)

def x402_protected(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        wallet_address = request.headers.get('X-Wallet-Address')
        signature = request.headers.get('X-Signature')
        challenge = request.headers.get('X-Challenge')

        # Check 1: Signature + Token gating (FREE for verified holders)
        if wallet_address and signature and challenge:
            from api_v1 import verify_signature
            if verify_signature(wallet_address, signature, challenge):
                holder_status = check_osai_holder(wallet_address)
                if holder_status["is_holder"]:
                    response = f(*args, **kwargs)
                    if isinstance(response, tuple):
                        resp, code = response
                        if isinstance(resp, Response):
                            resp.headers['X-Access-Tier'] = holder_status["tier"]
                            resp.headers['X-OSAI-Balance'] = str(holder_status["balance"])
                            resp.headers['X-Auth-Method'] = 'signature'
                            return resp, code
                        return resp, code
                    if isinstance(response, Response):
                        response.headers['X-Access-Tier'] = holder_status["tier"]
                        response.headers['X-OSAI-Balance'] = str(holder_status["balance"])
                        response.headers['X-Auth-Method'] = 'signature'
                    return response

        # Check 2: x402 Payment
        payment_header = request.headers.get('X-Payment') or request.headers.get('X-PAYMENT')
        if payment_header:
            valid, msg = verify_and_settle_payment(payment_header)
            if valid:
                response = f(*args, **kwargs)
                if isinstance(response, Response):
                    response.headers['X-Access-Tier'] = 'paid'
                    response.headers['X-Payment-Status'] = 'settled'
                return response
            return jsonify({"error": f"Payment failed: {msg}"}), 402

        # No valid auth - return 402
        payment_req = create_payment_requirements()
        response = jsonify(payment_req)
        response.status_code = 402
        response.headers['WWW-Authenticate'] = 'X402'
        return response

    return decorated_function
