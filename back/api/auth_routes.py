from flask import Blueprint, jsonify, request, g

from auth_utils import create_token, hash_password, token_required, verify_password
from db import execute, query_one


auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


def _validate_role(role: str) -> bool:
    return role in {"admin", "teacher", "student"}


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    role = str(payload.get("role", "student")).strip().lower()
    student_id = str(payload.get("student_id", "")).strip() or None
    course_id = str(payload.get("course_id", "")).strip() or None

    if not username or not password:
        return jsonify({"message": "username 和 password 不能为空"}), 400
    if len(password) < 6:
        return jsonify({"message": "password 长度至少为 6"}), 400
    if not _validate_role(role):
        return jsonify({"message": "role 必须是 admin/teacher/student"}), 400

    exists = query_one("SELECT user_id FROM sys_user WHERE username = %s", (username,))
    if exists:
        return jsonify({"message": "用户名已存在"}), 409

    if role == "student":
        if not student_id:
            return jsonify({"message": "学生角色必须提供 student_id"}), 400
        ok = query_one("SELECT student_id FROM student_info WHERE student_id = %s", (student_id,))
        if not ok:
            return jsonify({"message": "student_id 不存在"}), 400

    if role == "teacher":
        if not course_id:
            return jsonify({"message": "教师角色必须提供 course_id（示例: C101）"}), 400
        ok = query_one("SELECT Course_ID FROM teacher_profile_detail WHERE Course_ID = %s", (course_id,))
        if not ok:
            return jsonify({"message": "course_id 不存在"}), 400

    execute(
        """
        INSERT INTO sys_user(username, password_hash, role, student_id, course_id)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (username, hash_password(password), role, student_id, course_id),
    )

    return jsonify({"message": "注册成功"}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not username or not password:
        return jsonify({"message": "username 和 password 不能为空"}), 400

    user = query_one(
        """
        SELECT user_id, username, password_hash, role, student_id, course_id, is_active
        FROM sys_user
        WHERE username = %s
        """,
        (username,),
    )

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"message": "用户名或密码错误"}), 401

    if int(user["is_active"] or 0) != 1:
        return jsonify({"message": "账号已禁用"}), 403

    token = create_token(
        user_id=int(user["user_id"]),
        username=user["username"],
        role=user["role"],
        student_id=user.get("student_id"),
        course_id=user.get("course_id"),
    )

    execute(
        "INSERT INTO sys_login_log(user_id, username, login_ip) VALUES(%s, %s, %s)",
        (int(user["user_id"]), user["username"], request.remote_addr),
    )

    return jsonify(
        {
            "token": token,
            "user": {
                "user_id": int(user["user_id"]),
                "username": user["username"],
                "role": user["role"],
                "student_id": user.get("student_id"),
                "course_id": user.get("course_id"),
            },
        }
    )


@auth_bp.get("/me")
@token_required
def me():
    return jsonify({"user": g.current_user})
