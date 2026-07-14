from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable, Optional

import jwt
from flask import jsonify, request, g
from werkzeug.security import check_password_hash, generate_password_hash

from config import config


def hash_password(raw_password: str) -> str:
    return generate_password_hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, raw_password)


def create_token(user_id: int, username: str, role: str, student_id: Optional[str] = None, course_id: Optional[str] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "student_id": student_id,
        "course_id": course_id,
        "iat": now,
        "exp": now + timedelta(hours=config.jwt_expire_hours),
    }
    return jwt.encode(payload, config.jwt_secret_key, algorithm="HS256")


def parse_token(token: str):
    return jwt.decode(token, config.jwt_secret_key, algorithms=["HS256"])


def token_required(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "缺少或无效的 Authorization 头"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"message": "Token 不能为空"}), 401

        try:
            payload = parse_token(token)
            g.current_user = {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "student_id": payload.get("student_id"),
                "course_id": payload.get("course_id"),
            }
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token 已过期"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "无效 Token"}), 401

        return func(*args, **kwargs)

    return wrapper


def roles_required(*allowed_roles: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_role = (g.current_user or {}).get("role")
            if current_role not in allowed_roles:
                return jsonify({"message": "无权限访问该接口"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator
