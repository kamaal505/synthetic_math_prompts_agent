from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

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
        # No domain check: allow any Google account
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token") 