import hashlib
import hmac
import json
import secrets
from pathlib import Path


TEACHER_CREDENTIALS_FILE = Path(__file__).with_name("teachers.json")
PASSWORD_HASH_ITERATIONS = 600_000


def normalize_username(username):
    return username.strip().casefold()


def create_password_record(password):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return {"salt": salt.hex(), "password_hash": password_hash.hex()}


def load_teacher_credentials():
    try:
        data = json.loads(TEACHER_CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("Could not read teacher credentials") from error

    teachers = data.get("teachers") if isinstance(data, dict) else None
    if not isinstance(teachers, dict):
        raise RuntimeError("Teacher credentials must contain a teachers object")

    return {
        normalize_username(username): record
        for username, record in teachers.items()
        if isinstance(username, str) and isinstance(record, dict)
    }


def verify_teacher_credentials(username, password):
    record = load_teacher_credentials().get(normalize_username(username))
    if record is None:
        return False

    try:
        salt = bytes.fromhex(record["salt"])
        expected_hash = bytes.fromhex(record["password_hash"])
    except (KeyError, TypeError, ValueError):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return hmac.compare_digest(actual_hash, expected_hash)