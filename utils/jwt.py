from authlib.integrations.starlette_client import OAuth
from datetime import datetime, timedelta
from jose import JWTError, jwt

from config import settings

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_OAUTH_CONFIG["client_id"],
    client_secret=settings.GOOGLE_OAUTH_CONFIG["client_secret"],
    authorize_url=settings.GOOGLE_OAUTH_CONFIG["authorize_url"],
    authorize_params=None,
    access_token_url=settings.GOOGLE_OAUTH_CONFIG["token_url"],
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=settings.GOOGLE_OAUTH_CONFIG["redirect_uri"],
    client_kwargs={'scope': 'openid email profile'}
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