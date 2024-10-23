from authlib.integrations.starlette_client import OAuth
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from config import settings

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_OAUTH_CONFIG["client_id"],
    client_secret=settings.GOOGLE_OAUTH_CONFIG["client_secret"],
    authorize_url=settings.GOOGLE_OAUTH_CONFIG["authorize_url"],
    access_token_url=settings.GOOGLE_OAUTH_CONFIG["token_url"],
    redirect_uri=settings.GOOGLE_OAUTH_CONFIG["redirect_uri"],
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",  # Use this to fetch user info
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",  # URI to validate the JWT token
    client_kwargs={"scope": "openid email profile", }
)

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


# async def get_current_admin(request: Request):
#     token = request.session.get("jwt_token")  # Fetch JWT from session

#     if not token:
#         raise HTTPException(status_code=403, detail="Could not validate credentials")

#     try:
#         # Decode the JWT token
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         adm_email: str = payload.get("adm_email")
#         department: str = payload.get("department")
#         is_super_admin: bool = payload.get("is_super_admin")

#         if adm_email is None or department is None:
#             raise HTTPException(status_code=403, detail="Could not validate credentials")
        
#         # Return the decoded data as a dict
#         return {
#             "adm_email": adm_email,
#             "department": department,
#             "is_super_admin": is_super_admin
#         }

#     except JWTError:
#         raise HTTPException(status_code=403, detail="Could not validate credentials")


async def get_current_user(request: Request):
    token = request.session.get("jwt_token")  # Fetch JWT from session
    if not token:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Fetch user type
        user_type: str = payload.get("user_type")

        if user_type == "admin":
            # Admin-specific fields
            adm_email: str = payload.get("adm_email")
            department: str = payload.get("department")
            is_super_admin: bool = payload.get("is_super_admin")

            if adm_email is None or department is None:
                raise HTTPException(status_code=403, detail="Could not validate credentials")
            
            # Return admin data
            return {
                "user_type": "admin",
                "adm_email": adm_email,
                "department": department,
                "is_super_admin": is_super_admin
            }

        elif user_type == "student":
            # Student-specific fields
            email: str = payload.get("email")
            reg_number: str = payload.get("reg_number")

            if email is None or reg_number is None:
                raise HTTPException(status_code=403, detail="Could not validate credentials")

            # Return student data
            return {
                "user_type": "student",
                "email": email,
                "reg_number": reg_number
            }

        else:
            raise HTTPException(status_code=403, detail="Invalid user type")

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")