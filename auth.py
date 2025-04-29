from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import app
from database import get_db

# JWT Configuration
SECRET_KEY = "40yN26oQaW33VwJUhj2UdajWdw76Vt1o"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password Hashing: Uses bcrypt to securely store passwords.
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# User Authentication: Checks if the email & password match the stored user data.
def authenticate_user(db: Session, email: str, password: str):
    user = app.get_user(db, email)
    if not user or not verify_password(password, user.password):
        return False
    return user

# JWT Token Creation: Generates an access token for authenticated users.
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Token Verification: Decodes the token to identify the logged-in user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = app.get_user(db, email=email)
    if not user:
        raise credentials_exception
    return user
