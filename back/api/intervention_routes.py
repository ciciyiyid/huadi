from flask import Blueprint, jsonify, request, g

from auth_utils import roles_required, token_required
from db import execute, query_all


intervention_bp = Blueprint("intervention_bp", __name__, url_prefix="/api/interventions")


@intervention_bp.post("")
@token_required
@roles_required("admin")
def create_intervention():
    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("student_id", "")).strip()
    course_id = str(payload.get("course_id", "")).strip()
    warning_level = str(payload.get("warning_level", "")).strip()
    note = str(payload.get("note", "")).strip()
    operator = str(payload.get("operator", g.current_user.get("username", ""))).strip()

    if not student_id or not note:
        return jsonify({"message": "student_id 和 note 不能为空"}), 400

    execute(
        """
        INSERT INTO sys_intervention(student_id, course_id, warning_level, note, operator)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (student_id, course_id, warning_level, note, operator),
    )
    return jsonify({"message": "干预备注已保存"}), 201


@intervention_bp.get("")
@token_required
@roles_required("admin")
def list_interventions():
    student_id = request.args.get("student_id")
    page = max(1, int(request.args.get("page", 1)))
    page_size = max(1, min(50, int(request.args.get("page_size", 20))))
    offset = (page - 1) * page_size

    where = ""
    params = []
    if student_id:
        where = "WHERE student_id = %s"
        params.append(student_id)

    params.extend([page_size, offset])
    rows = query_all(
        f"""
        SELECT id, student_id, course_id, warning_level, note, operator, created_at
        FROM sys_intervention
        {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )
    return jsonify(rows)
