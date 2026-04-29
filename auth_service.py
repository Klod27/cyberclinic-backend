from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# ----------------------------------
# 🔐 CONFIG (MUST MATCH auth.py)
# ----------------------------------
SECRET_KEY = "your_secret_key"   # ⚠️ keep consistent with auth.py
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

# ----------------------------------
# PASSWORD HASHING
# ----------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------
# HASH PASSWORD
# ---------------------------
def hash_password(password: str):
    return pwd_context.hash(password)


# ---------------------------
# VERIFY PASSWORD
# ---------------------------
def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


# ---------------------------
# CREATE TOKEN (🔥 FIXED)
# ---------------------------
def create_access_token(user_id: int):

    payload = {
        "user_id": user_id,  # ✅ FIXED (was "sub")
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------
# VERIFY TOKEN (OPTIONAL USE)
# ---------------------------
def verify_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")  # ✅ FIXED

    except JWTError:
        return None