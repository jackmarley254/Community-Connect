# property/mpesa.py
import requests
import json
import base64
from datetime import datetime
from django.conf import settings

def get_access_token():
    """Generates an OAuth access token from Daraja."""
    consumer_key = settings.DARAJA_CONSUMER_KEY
    consumer_secret = settings.DARAJA_CONSUMER_SECRET
    api_url = f"{settings.DARAJA_API_URL}/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))
        response.raise_for_status() # Raise error for bad responses
        json_response = response.json()
        return json_response['access_token']
    except Exception as e:
        print(f"Error generating token: {e}")
        return None

def lipa_na_mpesa_online(phone_number, amount, account_reference, transaction_desc):
    """Initiates an STK Push."""
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    api_url = f"{settings.DARAJA_API_URL}/mpesa/stkpush/v1/processrequest"
    headers = { "Authorization": f"Bearer {access_token}" }

    # Generate Timestamp and Password
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = settings.DARAJA_PASSKEY
    shortcode = settings.DARAJA_BUSINESS_SHORTCODE
    password_str = f"{shortcode}{passkey}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode('utf-8')

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount), # Amount must be an integer
        "PartyA": phone_number, # Customer phone number
        "PartyB": shortcode, # Paybill number
        "PhoneNumber": phone_number,
        "CallBackURL": settings.DARAJA_CALLBACK_URL,
        "AccountReference": account_reference, # e.g., Invoice #123
        "TransactionDesc": transaction_desc
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}