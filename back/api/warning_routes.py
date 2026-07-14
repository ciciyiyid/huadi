from flask import Blueprint, jsonify, request

from auth_utils import roles_required, token_required
from db import query_all, query_one


warning_bp = Blueprint("warning_bp", __name__, url_prefix="/api/warnings")


@warning_bp.get("/students")
@token_required
@roles_required("admin", "teacher")
def student_warning_list():
    warning_level = request.args.get("warning_level")
    course_id = request.args.get("course_id")
    student_id = request.args.get("student_id")
    education_level = request.args.get("education_level")
    page = max(1, int(request.args.get("page", 1)))
    page_size = max(1, min(200, int(request.args.get("page_size", 20))))
    offset = (page - 1) * page_size

    where = []
    count_params = []
    if warning_level:
        where.append("w.warning_level = %s")
        count_params.append(warning_level)
    if course_id:
        where.append("w.Course_ID = %s")
        count_params.append(course_id)
    if student_id:
        where.append("w.Student_ID = %s")
        count_params.append(student_id)
    if education_level:
        where.append("si.education_level = %s")
        count_params.append(education_level)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total_row = query_one(
        f"""
        SELECT COUNT(*) AS total
        FROM student_warning_detail w
        LEFT JOIN student_info si ON w.Student_ID = si.student_id
        {where_sql}
        """,
        tuple(count_params),
    )
    total = total_row["total"] if total_row else 0

    rows = query_all(
        f"""
        SELECT w.Student_ID, w.Course_ID, w.Course_Name,
               si.education_level AS Education_Level,
               w.warning_level, CAST(w.risk_sum AS UNSIGNED) AS risk_sum,
               w.Quiz_Score_Avg, w.Assignment_Submission_Rate,
               w.Progress_Percentage, w.Video_Completion_Rate,
               w.is_login_risk, w.is_homework_risk,
               w.is_progress_risk, w.is_score_risk
        FROM student_warning_detail w
        LEFT JOIN student_info si ON w.Student_ID = si.student_id
        {where_sql}
        ORDER BY CAST(w.risk_sum AS UNSIGNED) DESC
        LIMIT %s OFFSET %s
        """,
        tuple(count_params + [page_size, offset]),
    )
    return jsonify({"total": total, "page": page, "page_size": page_size, "rows": rows})


@warning_bp.get("/levels")
@token_required
def warning_levels():
    rows = query_all(
        """
        SELECT warning_level, student_count, avg_score, avg_submit_rate,
               avg_progress, risk_ratio_pct
        FROM warning_level_summary
        ORDER BY student_count DESC
        """
    )
    return jsonify(rows)


@warning_bp.get("/courses")
@token_required
def warning_courses():
    rows = query_all(
        """
        SELECT r.Course_ID, r.Course_Name, r.student_count,
               r.high_risk_count, r.mid_risk_count, r.low_risk_count, r.safe_count,
               r.high_risk_pct, r.avg_quiz_score, r.avg_submit_rate, r.avg_progress,
               r.avg_video_completion AS avg_video_completion_rate,
               r.avg_study_hours AS avg_study_time_hours
        FROM course_risk_summary r
        ORDER BY r.high_risk_pct DESC
        """
    )
    return jsonify(rows)


@warning_bp.get("/education")
@token_required
def warning_education():
    rows = query_all(
        """
        SELECT Education_Level, student_count, ratio_pct,
               avg_total_study_hours, avg_quiz_score, avg_submit_rate,
               avg_progress, avg_video_completion,
               high_risk_pct, mid_risk_pct, low_risk_pct, safe_pct
        FROM education_risk_summary
        ORDER BY high_risk_pct DESC
        """
    )
    return jsonify(rows)


@warning_bp.get("/risk-dimensions")
@token_required
def risk_dimensions():
    """四维风险标记汇总：登录/作业/进度/成绩"""
    rows = query_all(
        """
        SELECT
            SUM(CASE WHEN is_login_risk = 1 THEN 1 ELSE 0 END)    AS login_risk_count,
            SUM(CASE WHEN is_homework_risk = 1 THEN 1 ELSE 0 END) AS homework_risk_count,
            SUM(CASE WHEN is_progress_risk = 1 THEN 1 ELSE 0 END) AS progress_risk_count,
            SUM(CASE WHEN is_score_risk = 1 THEN 1 ELSE 0 END)    AS score_risk_count,
            COUNT(*) AS total_count
        FROM student_warning_detail
        """
    )
    return jsonify(rows[0] if rows else {})
