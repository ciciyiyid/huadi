from flask import Blueprint, jsonify, request

from auth_utils import roles_required, token_required
from db import query_all, query_one


overview_bp = Blueprint("overview_bp", __name__, url_prefix="/api/overview")


@overview_bp.get("/metrics")
@token_required
@roles_required("admin", "teacher")
def metrics():
    data = {
        "student_count": query_one("SELECT COUNT(*) AS c FROM student_info")["c"],
        "course_count": query_one("SELECT COUNT(*) AS c FROM course_info")["c"],
        "high_risk_count": query_one("SELECT student_count AS c FROM warning_level_summary WHERE warning_level='高风险'")["c"],
        "avg_completion_rate": query_one("SELECT ROUND(AVG(completion_rate), 2) AS c FROM course_core_statistics")["c"],
    }
    return jsonify(data)


@overview_bp.get("/weekly-trend")
@token_required
def weekly_trend():
    limit = int(request.args.get("limit", 24))
    limit = max(1, min(limit, 200))

    rows = query_all(
        """
        SELECT week_label, learning_times, learner_count, total_study_time_hours, avg_quiz_score
        FROM weekly_learning_statistics
        ORDER BY stat_year, stat_week
        LIMIT %s
        """,
        (limit,),
    )
    return jsonify(rows)


@overview_bp.get("/course-enrollment")
@token_required
def course_enrollment():
    rows = query_all(
        """
        SELECT enrollment_rank, course_id, course_name, learner_count
        FROM course_enrollment_ranking
        ORDER BY enrollment_rank
        """
    )
    return jsonify(rows)


@overview_bp.get("/warning-distribution")
@token_required
def warning_distribution():
    rows = query_all(
        """
        SELECT warning_level, student_count, risk_ratio_pct
        FROM warning_level_summary
        ORDER BY student_count DESC
        """
    )
    return jsonify(rows)
