from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import os

ALLOWED_PEOPLE_FILE = os.path.join(os.path.dirname(__file__), '../allowed_people.txt')

# Cache the allowed emails list
_allowed_emails = None

def get_allowed_emails():
    global _allowed_emails
    if _allowed_emails is None:
        with open(ALLOWED_PEOPLE_FILE, 'r') as f:
            _allowed_emails = set(line.strip().lower() for line in f if line.strip())
    return _allowed_emails

async def verify_company_email(request: Request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    scheme, token = get_authorization_scheme_param(auth)
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request())
        email = idinfo.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No email in token")
        allowed_emails = get_allowed_emails()
        if email.lower() not in allowed_emails:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not allowed")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token") 