import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta

from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY", "cyberclinic_demo_secret_key_change_later")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"pbkdf2_sha256${salt}${hashed}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, original_hash = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

        return hmac.compare_digest(new_hash, original_hash)

    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")

    except JWTError:
        return None