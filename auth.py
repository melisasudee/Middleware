from functools import wraps

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from extensions import db
from models import ApiKey


def _env_api_keys():
    return set(current_app.config.get("API_KEYS", []))


def check_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    api_key = api_key.strip()
    if api_key in _env_api_keys():
        return True

    try:
        stored = ApiKey.query.filter_by(key=api_key, active=True).first()
    except Exception:
        return False
    return bool(stored)


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get(current_app.config.get("API_KEY_HEADER", "X-API-KEY")) or request.args.get("api_key")
        jwt_identity = None
        try:
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
        except Exception:
            jwt_identity = None

        if jwt_identity or check_api_key(api_key):
            return func(*args, **kwargs)

        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    return wrapper
