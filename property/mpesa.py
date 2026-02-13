import requests
import base64
from datetime import datetime
from django.conf import settings

def get_access_token(consumer_key, consumer_secret):
    """
    Generates a dynamic access token using the provided credentials.
    """
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    if settings.DARAJA_ENVIRONMENT == 'production':
        api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        r = requests.get(api_url, auth=(consumer_key, consumer_secret))
        r.raise_for_status()
        return r.json()['access_token']
    except Exception as e:
        print(f"M-Pesa Auth Error: {e}")
        return None

def lipa_na_mpesa_online(phone_number, amount, account_reference, transaction_desc, consumer_key, consumer_secret, business_shortcode, passkey):
    """
    Triggers STK Push using DYNAMIC credentials (per organization).
    """
    access_token = get_access_token(consumer_key, consumer_secret)
    if not access_token:
        return {'ResponseCode': '1', 'errorMessage': 'Failed to authenticate with Safaricom.'}
    
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    if settings.DARAJA_ENVIRONMENT == 'production':
        api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{business_shortcode}{passkey}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode('utf-8')
    
    headers = { 'Authorization': f'Bearer {access_token}' }
    
    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": business_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.DARAJA_CALLBACK_URL, # Central callback
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    
    try:
        r = requests.post(api_url, json=payload, headers=headers)
        return r.json()
    except Exception as e:
        return {'ResponseCode': '1', 'errorMessage': str(e)}